"""Gemini integration uses mocked HTTP only; no credentials or live quota required."""
import asyncio
import json
import unittest
from unittest.mock import patch

import httpx

from backend.ai_provider import GeminiExplanationProvider, configured_provider
from backend.customer import customer_journey
from backend.data import prepare_context
from backend.engine import compare_access, default_scenario, evaluate
from backend.explanations import ExplanationService, build_context, explain


class GeminiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        prepared = prepare_context()
        cls.clear = evaluate(prepared, default_scenario(prepared))
        cls.restricted = evaluate(prepared, default_scenario(prepared, access='restricted',scenario_revision=2))
        cls.blocked = evaluate(prepared, default_scenario(prepared, access='blocked',scenario_revision=3))
        cls.context = build_context(cls.clear,customer_journey(cls.clear))

    def provider(self, handler):
        return GeminiExplanationProvider('test-secret-not-real','gemini-test-flash',httpx.MockTransport(handler))

    def payload(self, context=None, intent='risk', refs=None):
        return {'result_id':(context or self.context).result_id,'intent':intent,'supporting_refs':refs or ['risk-storm-scenario']}

    def response(self, selection):
        return httpx.Response(200,json={'candidates':[{'finishReason':'STOP','content':{'role':'model','parts':[{'text':json.dumps(selection)}]}}]})

    def answer(self, provider, context=None, question='What does HIGH mean?'):
        return asyncio.run(explain(context or self.context,question,provider))

    def test_request_header_schema_and_minimum_context(self):
        def handler(request):
            self.assertEqual(request.headers['x-goog-api-key'],'test-secret-not-real')
            self.assertNotIn('test-secret',str(request.url))
            body=json.loads(request.content)
            self.assertNotIn('test-secret',request.content.decode())
            self.assertNotIn('tools',body)
            schema=body['generationConfig']['responseJsonSchema']
            self.assertFalse(schema['additionalProperties'])
            self.assertEqual(schema['properties']['result_id']['enum'],[self.context.result_id])
            self.assertEqual(body['generationConfig']['responseMimeType'],'application/json')
            context=json.loads(body['contents'][0]['parts'][0]['text'])
            self.assertEqual(set(context),{'result_id','intent','restoration_status','dataset_note','allowed_clauses'})
            self.assertTrue(all(c['id'].startswith('risk-') for c in context['allowed_clauses']))
            self.assertNotIn('location_label',context)
            return self.response(self.payload())
        self.assertEqual(self.answer(self.provider(handler)).mode,'ai_assisted')

    def test_http_errors_and_timeout_are_sanitized_fallbacks(self):
        for status in [400,401,403,404,429,500,503]:
            provider=self.provider(lambda request:httpx.Response(status,json={'error':'test-secret-not-real'}))
            response=self.answer(provider)
            self.assertEqual(response.mode,'standard')
            self.assertNotIn('test-secret',response.model_dump_json())
        def timeout(request): raise httpx.ReadTimeout('test-secret-not-real')
        self.assertEqual(self.answer(self.provider(timeout)).fallback_reason,'timeout')

    def test_opaque_signature_is_discarded_but_text_is_still_validated(self):
        response=self.response(self.payload()).json()
        response['candidates'][0]['content']['parts'][0]['thoughtSignature']='opaque-transport-metadata'
        answer=self.answer(self.provider(lambda request:httpx.Response(200,json=response)))
        self.assertEqual(answer.mode,'ai_assisted')
        self.assertNotIn('opaque-transport',answer.model_dump_json())
        response['candidates'][0]['content']['parts'][0]['text']='{"answer":"Power returns at noon"}'
        self.assertEqual(self.answer(self.provider(lambda request:httpx.Response(200,json=response))).mode,'standard')

    def test_invalid_json_schema_reference_and_stale_result_fall_back(self):
        outputs=[httpx.Response(200,content='invalid'), self.response({}),
                 self.response({**self.payload(),'supporting_refs':['invented']}),
                 self.response({**self.payload(),'result_id':'stale'}),
                 self.response({**self.payload(),'answer':'Your outage probability is 90%.'})]
        for output in outputs:
            self.assertEqual(self.answer(self.provider(lambda request:output)).mode,'standard')

    def test_blocked_truncated_thought_or_tool_output_is_rejected(self):
        outputs=[{'promptFeedback':{'blockReason':'SAFETY'}}, {'candidates':[]},
            {'candidates':[{'finishReason':'MAX_TOKENS'}]},
            {'candidates':[{'finishReason':'STOP','content':{'role':'model','parts':[{'thought':True,'text':'private reasoning'}]}}]},
            {'candidates':[{'finishReason':'STOP','content':{'role':'model','parts':[{'functionCall':{}}]}}]}]
        for output in outputs:
            self.assertEqual(self.answer(self.provider(lambda request:httpx.Response(200,json=output))).mode,'standard')

    def test_all_four_questions_through_gemini_preserve_engine_values(self):
        comparison=compare_access(self.clear,self.restricted)
        restricted=build_context(self.restricted,customer_journey(self.restricted,self.clear,comparison),comparison)
        blocked=build_context(self.blocked,customer_journey(self.blocked))
        cases=[(self.context,'Why is restoration 11–18 hours?','restoration',['repair-scope'],'11–18'),
               (restricted,'Why did my restoration outlook change?','change',['comparison-summary'],'16–25'),
               (blocked,'When will my power be restored?','availability',['access-detail'],'Access must be cleared'),
               (self.context,'What does HIGH mean?','risk',['risk-storm-scenario'],'not an outage probability')]
        for context,question,intent,refs,expected in cases:
            output=self.response(self.payload(context,intent,refs))
            answer=self.answer(self.provider(lambda request:output),context,question)
            self.assertEqual(answer.mode,'ai_assisted')
            self.assertIn(expected,answer.answer)
        self.assertIsNone(blocked.restoration_bounds)

    def test_default_gemini_configuration_and_no_key_no_model_fallback(self):
        for values in [{},{'GRIDGUIDE_AI_MODEL':'gemini-test-flash'}, {'GEMINI_API_KEY':'test-only','GRIDGUIDE_AI_MODEL':''}]:
            with patch.dict('os.environ',values,clear=True): self.assertIsNone(configured_provider())
        with patch.dict('os.environ',{'GEMINI_API_KEY':'test-only','GRIDGUIDE_AI_MODEL':'gemini-test-flash'},clear=True):
            self.assertIsInstance(configured_provider(),GeminiExplanationProvider)
        with patch.dict('os.environ',{'GEMINI_API_KEY':'test-only'},clear=True):
            self.assertIsInstance(configured_provider(),GeminiExplanationProvider)
        with patch.dict('os.environ',{'GEMINI_API_KEY':'test-only','GRIDGUIDE_AI_PROVIDER':'none','GRIDGUIDE_AI_MODEL':'gemini-test-flash'},clear=True):
            self.assertIsNone(configured_provider())
        for model in ['gemini-pro','https://evil.example/flash','../gemini-flash?key=secret']:
            with self.assertRaises(ValueError): GeminiExplanationProvider('test-only',model)

    def test_cache_bounded_expiring_and_comparison_sensitive(self):
        calls=[]
        class Fake:
            async def select(inner,context,intent,refs):
                calls.append(context.result_id)
                return json.dumps({'result_id':context.result_id,'intent':intent,'supporting_refs':list(refs[:3])})
        async def run():
            service=ExplanationService(Fake(),max_entries=2,ttl=300)
            first=await service.answer(self.context,'What does HIGH mean?')
            self.assertEqual(first,await service.answer(self.context,'What does HIGH mean?'))
            self.assertEqual(len(calls),1)
            changed=self.context.model_copy(update={'scenario_revision':99})
            await service.answer(changed,'What does HIGH mean?')
            await service.answer(self.context,'Why did my estimate change?')
            self.assertEqual(len(service._cache),2)
            # Even the same result ID must not reuse an answer for different comparison text.
            clause=self.context.clauses[0].model_copy(update={'text':'Changed policy text'})
            changed=self.context.model_copy(update={'clauses':(clause,*self.context.clauses[1:])})
            await service.answer(changed,'What does HIGH mean?')
            self.assertEqual(len(calls),4)
            with patch('backend.explanations.time.monotonic',return_value=10**12):
                await service.answer(changed,'What does HIGH mean?')
            self.assertEqual(len(calls),5)
        asyncio.run(run())

    def test_invalid_answers_are_not_cached(self):
        calls=[]
        class Bad:
            async def select(self,*args): calls.append(1); return '{}'
        async def run():
            service=ExplanationService(Bad())
            for _ in range(2):
                self.assertEqual((await service.answer(self.context,'What does HIGH mean?')).mode,'standard')
            self.assertEqual(len(service._cache),0)
        asyncio.run(run())
        self.assertEqual(len(calls),2)
