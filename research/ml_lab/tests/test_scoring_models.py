import unittest
from unittest.mock import patch
import numpy as np
from sklearn.base import clone

from benchmarks.policies import POLICIES
from research.ml_lab.generator import generate_suite
from research.ml_lab.features import extract_features, FEATURE_NAMES
from research.ml_lab.labels import evaluate_problem
from research.ml_lab.models import catalog, matrix, predict
from research.ml_lab.scoring import summarize, paired


class ScoringModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.problem = generate_suite('smoke')[0].problem
        cls.row = dict(evaluate_problem(cls.problem),group_id='g1')

    def test_common_case_denominator_is_mandatory(self):
        for fn in (lambda rows,ps:summarize(rows,ps),lambda rows,ps:paired(rows,ps,POLICIES[0])):
            for predictions in ([POLICIES[0]], [POLICIES[0],None], [POLICIES[0],'fake']):
                with self.assertRaises(ValueError):
                    fn([self.row,self.row],predictions)

    def test_zero_fixed_regret_does_not_invent_percentage(self):
        result=paired([self.row],[self.row['label']],self.row['label'])
        self.assertEqual(result['fixed_mean_regret_customer_hours'],0)
        self.assertIsNone(result['relative_regret_improvement'])
        self.assertEqual(result['gate'],'UNTESTABLE')

    def test_oracle_and_ties(self):
        result=summarize([self.row],[self.row['label']])
        self.assertEqual(result['absolute_regret_customer_hours']['mean'],0)
        self.assertEqual(result['tie_aware_accuracy'],1)
        self.assertEqual(result['predicted'],1)

    def test_matrix_rejects_metadata_and_nonfinite(self):
        features=extract_features(self.problem)
        self.assertEqual(matrix([{'features':features}]).shape,(1,len(FEATURE_NAMES)))
        for corrupt in ({**features,'label':0},{**features,'task_count':np.inf}):
            with self.assertRaises(ValueError):
                matrix([{'features':corrupt}])

    def test_catalog_and_inference_fail_closed(self):
        self.assertEqual(len(catalog()),8)
        p=self.problem.model_dump(mode='json')
        p['tasks'][0]['access']='blocked'
        # Unsupported scope never invokes an unfitted estimator.
        self.assertIsNone(predict(next(iter(catalog().values())),p))
        p['unexpected_outcome']=42
        with self.assertRaises(ValueError):
            predict(next(iter(catalog().values())),p)

    def test_scaler_fits_only_supplied_training_matrix(self):
        model=catalog()['logistic-c1']
        train=np.zeros((8,len(FEATURE_NAMES)))
        train[:,0]=np.arange(8)
        model.fit(train,np.array([POLICIES[0],POLICIES[1]]*4))
        self.assertEqual(model.named_steps['scale'].mean_[0],3.5)
        model.predict(np.full((2,len(FEATURE_NAMES)),1e8))
        self.assertEqual(model.named_steps['scale'].mean_[0],3.5)


if __name__=='__main__':
    unittest.main()
