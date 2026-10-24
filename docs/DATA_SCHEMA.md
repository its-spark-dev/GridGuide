# Exact GIS field inventory

Snapshot audited 2026-10-24. Generated from the read-only audit. Full interpretations and joins are in [DATA_AUDIT.md](DATA_AUDIT.md). Names below are exact DBF names; C = character, N = numeric integer, F = floating numeric, D = date. Missing means null/blank, not a sentinel category. No customer/contact values are included.

## Data1.zip / Ambulance_Servi_Pairwis_Clip.shp

10 features; POINTZ; horizontal CRS EPSG:3857.

| Field | DBF type / width / decimals | Missing | Distinct nonmissing |
|---|---|---:|---:|
| `PERMANENT_` | C / 40 / 0 | 0 | 10 |
| `SOURCE_FEA` | C / 40 / 0 | 9 | 1 |
| `SOURCE_DAT` | C / 40 / 0 | 0 | 8 |
| `SOURCE_D_1` | C / 100 / 0 | 0 | 8 |
| `SOURCE_ORI` | C / 130 / 0 | 0 | 1 |
| `DATA_SECUR` | N / 5 / 0 | 0 | 1 |
| `DISTRIBUTI` | C / 4 / 0 | 10 | 0 |
| `LOADDATE` | D / 8 / 0 | 0 | 8 |
| `FTYPE` | N / 10 / 0 | 0 | 1 |
| `FCODE` | N / 10 / 0 | 0 | 1 |
| `NAME` | C / 100 / 0 | 0 | 10 |
| `ISLANDMARK` | N / 10 / 0 | 0 | 1 |
| `POINTLOCAT` | N / 10 / 0 | 0 | 1 |
| `ADMINTYPE` | N / 10 / 0 | 0 | 1 |
| `ADDRESSBUI` | C / 60 / 0 | 10 | 0 |
| `ADDRESS` | C / 75 / 0 | 0 | 10 |
| `CITY` | C / 40 / 0 | 0 | 8 |
| `STATE` | C / 2 / 0 | 0 | 1 |
| `ZIPCODE` | C / 10 / 0 | 0 | 9 |
| `GNIS_ID` | C / 10 / 0 | 1 | 9 |
| `FOOT_ID` | C / 40 / 0 | 10 | 0 |
| `COMPLEX_ID` | C / 40 / 0 | 10 | 0 |

## Data1.zip / arcos_prod_damage_09_28_Clip.shp

1,659 features; POINTZ; horizontal CRS EPSG:4326.

| Field | DBF type / width / decimals | Missing | Distinct nonmissing |
|---|---|---:|---:|
| `Outage_Num` | F / 19 / 11 | 0 | 1 |
| `Incident_W` | F / 19 / 11 | 0 | 1 |
| `Event` | C / 254 / 0 | 0 | 1 |
| `Region` | C / 254 / 0 | 0 | 1 |
| `District` | C / 254 / 0 | 1,659 | 0 |
| `Crew_Area` | C / 254 / 0 | 1,659 | 0 |
| `Substation` | C / 254 / 0 | 0 | 29 |
| `Circuit` | C / 254 / 0 | 0 | 85 |
| `Report_Tim` | D / 8 / 0 | 0 | 55 |
| `Reporting_` | C / 254 / 0 | 1,659 | 0 |
| `Reporting1` | C / 254 / 0 | 1,659 | 0 |
| `TASK_Crew` | C / 254 / 0 | 1,659 | 0 |
| `TASK_Job_I` | C / 254 / 0 | 1,659 | 0 |
| `Status` | C / 254 / 0 | 1,659 | 0 |
| `Repaired` | C / 254 / 0 | 0 | 2 |
| `Repaired_D` | D / 8 / 0 | 0 | 55 |
| `Repaired_B` | C / 254 / 0 | 1,659 | 0 |
| `Asset_Type` | C / 254 / 0 | 1 | 10 |
| `Inform_Wor` | C / 254 / 0 | 0 | 5 |
| `Media` | F / 19 / 11 | 0 | 7 |
| `Access_Iss` | C / 254 / 0 | 1 | 2 |
| `Special_Eq` | C / 254 / 0 | 1,373 | 9 |
| `Longitude` | F / 19 / 11 | 0 | 1,556 |
| `Latitude` | F / 19 / 11 | 0 | 1,556 |
| `NEAR_FID` | N / 10 / 0 | 0 | 1,347 |
| `NEAR_DIST` | F / 19 / 11 | 0 | 1,229 |

## Data1.zip / Customer_Clip.shp

117,642 features; POINTZ; horizontal CRS EPSG:4326.

| Field | DBF type / width / decimals | Missing | Distinct nonmissing |
|---|---|---:|---:|
| `id` | N / 10 / 0 | 0 | 117,642 |
| `critical_c` | C / 15 / 0 | 0 | 2 |
| `special_op` | C / 23 / 0 | 117,642 | 0 |
| `aep_locati` | C / 17 / 0 | 0 | 49,489 |
| `aep_xfmr_l` | C / 17 / 0 | 0 | 25,309 |
| `road_id` | N / 10 / 0 | 0 | 5,443 |
| `aep_string` | N / 10 / 0 | 0 | 6 |
| `customer_c` | N / 10 / 0 | 0 | 29 |
| `address` | C / 100 / 0 | 117,642 | 0 |
| `road_name` | C / 100 / 0 | 65 | 3,558 |
| `city` | C / 20 / 0 | 0 | 30 |
| `state` | C / 2 / 0 | 0 | 3 |
| `circuit_id` | C / 20 / 0 | 0 | 110 |
| `kind_of_se` | C / 11 / 0 | 0 | 3 |
| `address_nu` | C / 9 / 0 | 117,642 | 0 |
| `service_po` | F / 19 / 11 | 0 | 49,490 |
| `service__1` | F / 19 / 11 | 0 | 49,490 |
| `street_cod` | C / 7 / 0 | 65 | 4,599 |
| `macss_mete` | C / 26 / 0 | 117,642 | 0 |
| `anno_strin` | C / 100 / 0 | 0 | 24,564 |
| `rotation` | F / 19 / 11 | 0 | 105,407 |
| `esri_defau` | C / 50 / 0 | 0 | 2 |
| `eo_source_` | C / 35 / 0 | 0 | 1 |
| `premise_nu` | C / 20 / 0 | 0 | 117,642 |

## Data1.zip / Fire_Stations_E_Pairwis_Clip.shp

37 features; POINTZ; horizontal CRS EPSG:3857.

| Field | DBF type / width / decimals | Missing | Distinct nonmissing |
|---|---|---:|---:|
| `PERMANENT_` | C / 40 / 0 | 0 | 37 |
| `SOURCE_FEA` | C / 40 / 0 | 32 | 1 |
| `SOURCE_DAT` | C / 40 / 0 | 0 | 36 |
| `SOURCE_D_1` | C / 100 / 0 | 0 | 15 |
| `SOURCE_ORI` | C / 130 / 0 | 0 | 1 |
| `DATA_SECUR` | N / 5 / 0 | 0 | 1 |
| `DISTRIBUTI` | C / 4 / 0 | 37 | 0 |
| `LOADDATE` | D / 8 / 0 | 0 | 15 |
| `FTYPE` | N / 10 / 0 | 0 | 1 |
| `FCODE` | N / 10 / 0 | 0 | 1 |
| `NAME` | C / 100 / 0 | 0 | 37 |
| `ISLANDMARK` | N / 10 / 0 | 0 | 1 |
| `POINTLOCAT` | N / 10 / 0 | 0 | 1 |
| `ADMINTYPE` | N / 10 / 0 | 0 | 1 |
| `ADDRESSBUI` | C / 60 / 0 | 37 | 0 |
| `ADDRESS` | C / 75 / 0 | 0 | 37 |
| `CITY` | C / 40 / 0 | 0 | 15 |
| `STATE` | C / 2 / 0 | 0 | 1 |
| `ZIPCODE` | C / 10 / 0 | 0 | 21 |
| `GNIS_ID` | C / 10 / 0 | 0 | 37 |
| `FOOT_ID` | C / 40 / 0 | 37 | 0 |
| `COMPLEX_ID` | C / 40 / 0 | 37 | 0 |

## Data1.zip / Fuse_Bank_Clip.shp

7,616 features; POINTZ; horizontal CRS EPSG:4326.

| Field | DBF type / width / decimals | Missing | Distinct nonmissing |
|---|---|---:|---:|
| `id` | N / 10 / 0 | 0 | 7,616 |
| `device_typ` | C / 21 / 0 | 0 | 1 |
| `location_n` | C / 21 / 0 | 0 | 6,698 |
| `existing_p` | C / 14 / 0 | 12 | 7 |
| `aep_west_e` | C / 30 / 0 | 7,616 | 0 |
| `aep_west_l` | C / 21 / 0 | 7,616 | 0 |
| `circuit_id` | C / 32 / 0 | 0 | 109 |
| `circuit__1` | C / 32 / 0 | 7,615 | 1 |
| `aep_statio` | C / 40 / 0 | 0 | 31 |
| `aep_circui` | C / 64 / 0 | 0 | 109 |
| `scada_cont` | C / 12 / 0 | 0 | 7,616 |
| `normal_sta` | C / 16 / 0 | 0 | 2 |
| `owner_name` | C / 50 / 0 | 0 | 1 |
| `mirrored_i` | C / 7 / 0 | 6,677 | 1 |
| `aep_out_of` | C / 7 / 0 | 0 | 1 |
| `aep_switch` | C / 10 / 0 | 7,616 | 0 |
| `a_phase_sp` | C / 32 / 0 | 3,898 | 22 |
| `b_phase_sp` | C / 32 / 0 | 4,107 | 22 |
| `c_phase_sp` | C / 32 / 0 | 4,076 | 21 |
| `a_phase_da` | D / 8 / 0 | 6,829 | 384 |
| `b_phase_da` | D / 8 / 0 | 6,904 | 320 |
| `c_phase_da` | D / 8 / 0 | 6,888 | 321 |
| `upstream_l` | C / 21 / 0 | 19 | 1,922 |
| `aep_custom` | N / 10 / 0 | 0 | 241 |
| `rotation` | F / 19 / 11 | 0 | 7,616 |
| `esri_defau` | C / 70 / 0 | 0 | 3 |
| `eo_source_` | C / 35 / 0 | 0 | 1 |
| `status` | C / 17 / 0 | 0 | 1 |
| `owner_type` | C / 14 / 0 | 0 | 1 |
| `mounting` | C / 11 / 0 | 0 | 3 |
| `network_ty` | C / 10 / 0 | 0 | 1 |
| `nominal_vo` | C / 9 / 0 | 3 | 3 |
| `global_id` | C / 38 / 0 | 0 | 7,616 |

## Data1.zip / Hospitals_Medic_Pairwis_Clip.shp

5 features; POINTZ; horizontal CRS EPSG:3857.

| Field | DBF type / width / decimals | Missing | Distinct nonmissing |
|---|---|---:|---:|
| `PERMANENT_` | C / 40 / 0 | 0 | 5 |
| `SOURCE_FEA` | C / 40 / 0 | 5 | 0 |
| `SOURCE_DAT` | C / 40 / 0 | 0 | 5 |
| `SOURCE_D_1` | C / 100 / 0 | 0 | 5 |
| `SOURCE_ORI` | C / 130 / 0 | 0 | 1 |
| `DATA_SECUR` | N / 5 / 0 | 0 | 1 |
| `DISTRIBUTI` | C / 4 / 0 | 5 | 0 |
| `LOADDATE` | D / 8 / 0 | 0 | 5 |
| `FTYPE` | N / 10 / 0 | 0 | 1 |
| `FCODE` | N / 10 / 0 | 0 | 1 |
| `NAME` | C / 100 / 0 | 0 | 5 |
| `ISLANDMARK` | N / 10 / 0 | 0 | 1 |
| `POINTLOCAT` | N / 10 / 0 | 0 | 1 |
| `ADMINTYPE` | N / 10 / 0 | 0 | 1 |
| `ADDRESSBUI` | C / 60 / 0 | 5 | 0 |
| `ADDRESS` | C / 75 / 0 | 0 | 5 |
| `CITY` | C / 40 / 0 | 0 | 3 |
| `STATE` | C / 2 / 0 | 0 | 1 |
| `ZIPCODE` | C / 10 / 0 | 0 | 4 |
| `GNIS_ID` | C / 10 / 0 | 0 | 5 |
| `FOOT_ID` | C / 40 / 0 | 5 | 0 |
| `COMPLEX_ID` | C / 40 / 0 | 5 | 0 |

## Data1.zip / Pole_Clip.shp

107,013 features; POINTZ; horizontal CRS EPSG:4326.

| Field | DBF type / width / decimals | Missing | Distinct nonmissing |
|---|---|---:|---:|
| `id` | N / 10 / 0 | 0 | 107,013 |
| `status` | C / 17 / 0 | 0 | 1 |
| `location_n` | C / 21 / 0 | 0 | 107,013 |
| `usage` | C / 24 / 0 | 0 | 7 |
| `number` | C / 20 / 0 | 107,013 | 0 |
| `owner_name` | C / 120 / 0 | 0 | 18 |
| `date_insta` | D / 8 / 0 | 53,249 | 9,417 |
| `date_ins_1` | C / 15 / 0 | 53,249 | 9,417 |
| `aep_moved_` | C / 7 / 0 | 0 | 3 |
| `material` | C / 18 / 0 | 0 | 11 |
| `aep_plant_` | C / 31 / 0 | 107,013 | 0 |
| `height` | C / 8 / 0 | 1 | 35 |
| `class` | C / 11 / 0 | 1 | 16 |
| `treatment` | C / 21 / 0 | 107,013 | 0 |
| `aep_ciac` | C / 4 / 0 | 107,013 | 0 |
| `ciac_date` | D / 8 / 0 | 107,013 | 0 |
| `date_manuf` | D / 8 / 0 | 22,856 | 105 |
| `reinforcem` | C / 25 / 0 | 103,973 | 1 |
| `esri_defau` | C / 35 / 0 | 0 | 4 |
| `eo_source_` | C / 35 / 0 | 0 | 1 |
| `rotation` | F / 19 / 11 | 0 | 106,968 |
| `owner_type` | C / 14 / 0 | 0 | 3 |
| `global_id` | C / 38 / 0 | 0 | 107,013 |

## Data1.zip / Primary_ExportFeatures.shp

62,788 features; POLYLINE; horizontal CRS EPSG:4326.

| Field | DBF type / width / decimals | Missing | Distinct nonmissing |
|---|---|---:|---:|
| `id` | N / 10 / 0 | 0 | 62,788 |
| `status` | C / 17 / 0 | 0 | 1 |
| `network_ty` | C / 10 / 0 | 0 | 1 |
| `nominal_vo` | C / 9 / 0 | 322 | 5 |
| `usage` | C / 22 / 0 | 1 | 3 |
| `phase_orde` | C / 14 / 0 | 9,555 | 34 |
| `existing_p` | C / 14 / 0 | 587 | 7 |
| `circuit_id` | C / 32 / 0 | 0 | 115 |
| `aep_statio` | C / 40 / 0 | 0 | 33 |
| `aep_circui` | C / 64 / 0 | 0 | 115 |
| `aep_stat_1` | N / 10 / 0 | 0 | 33 |
| `aep_constr` | C / 41 / 0 | 0 | 12 |
| `owner_name` | C / 50 / 0 | 3 | 2 |
| `mounting` | C / 11 / 0 | 0 | 2 |
| `report_len` | F / 19 / 11 | 0 | 61,445 |
| `a_phase_sp` | C / 32 / 0 | 27,650 | 152 |
| `b_phase_sp` | C / 32 / 0 | 29,195 | 149 |
| `c_phase_sp` | C / 32 / 0 | 29,288 | 145 |
| `u_phase_sp` | C / 32 / 0 | 62,692 | 13 |
| `n_phase_sp` | C / 32 / 0 | 8,523 | 142 |
| `aep_date_i` | D / 8 / 0 | 171 | 3,155 |
| `treatment_` | D / 8 / 0 | 62,738 | 12 |
| `eo_source_` | C / 35 / 0 | 0 | 2 |
| `esri_defau` | C / 35 / 0 | 0 | 6 |
| `owner_type` | C / 14 / 0 | 0 | 3 |
| `aep_design` | C / 14 / 0 | 0 | 6 |
| `aep_poly_p` | C / 7 / 0 | 0 | 1 |
| `aep_positi` | N / 10 / 0 | 0 | 5 |
| `existing_n` | C / 7 / 0 | 0 | 4 |
| `location_n` | C / 24 / 0 | 80 | 46,283 |
| `location_1` | C / 24 / 0 | 960 | 51,833 |
| `shared_neu` | N / 10 / 0 | 0 | 12,997 |
| `cable_coun` | N / 10 / 0 | 0 | 3 |
| `n_cable_co` | N / 10 / 0 | 0 | 3 |
| `global_id` | C / 38 / 0 | 0 | 62,788 |
| `estimated_` | C / 7 / 0 | 62,788 | 0 |
| `Shape_Leng` | F / 19 / 11 | 0 | 62,788 |

## Data2.zip / Recloser_Bank_Clip.shp

331 features; POINTZ; horizontal CRS EPSG:4326.

| Field | DBF type / width / decimals | Missing | Distinct nonmissing |
|---|---|---:|---:|
| `id` | N / 10 / 0 | 0 | 331 |
| `type` | C / 9 / 0 | 0 | 1 |
| `location_n` | C / 21 / 0 | 0 | 330 |
| `device_typ` | C / 32 / 0 | 0 | 2 |
| `circuit_id` | C / 32 / 0 | 0 | 77 |
| `circuit__1` | C / 32 / 0 | 328 | 3 |
| `aep_statio` | C / 40 / 0 | 0 | 30 |
| `aep_circui` | C / 64 / 0 | 0 | 77 |
| `scada_cont` | C / 12 / 0 | 331 | 0 |
| `owner_name` | C / 50 / 0 | 0 | 1 |
| `normal_sta` | C / 16 / 0 | 0 | 2 |
| `existing_p` | C / 14 / 0 | 0 | 7 |
| `aep_switch` | C / 50 / 0 | 329 | 2 |
| `aep_out_of` | C / 7 / 0 | 0 | 1 |
| `aep_distri` | C / 7 / 0 | 0 | 2 |
| `aep_west_l` | C / 21 / 0 | 331 | 0 |
| `aep_west_r` | C / 10 / 0 | 331 | 0 |
| `bypass_nor` | C / 9 / 0 | 0 | 1 |
| `a_phase_sp` | C / 32 / 0 | 89 | 38 |
| `b_phase_sp` | C / 32 / 0 | 101 | 34 |
| `c_phase_sp` | C / 32 / 0 | 108 | 34 |
| `a_phase_da` | D / 8 / 0 | 107 | 206 |
| `b_phase_da` | D / 8 / 0 | 115 | 205 |
| `c_phase_da` | D / 8 / 0 | 120 | 200 |
| `upstream_l` | C / 21 / 0 | 3 | 121 |
| `aep_custom` | N / 10 / 0 | 0 | 238 |
| `rotation` | F / 19 / 11 | 0 | 331 |
| `esri_defau` | C / 70 / 0 | 0 | 3 |
| `eo_source_` | C / 35 / 0 | 0 | 1 |
| `owner_type` | C / 14 / 0 | 0 | 1 |
| `status` | C / 10 / 0 | 0 | 1 |
| `nominal_vo` | C / 9 / 0 | 0 | 3 |
| `aep_time_d` | C / 12 / 0 | 96 | 3 |
| `aep_time_1` | C / 8 / 0 | 96 | 2 |
| `aep_instan` | C / 12 / 0 | 96 | 1 |
| `aep_inst_1` | C / 8 / 0 | 96 | 1 |
| `global_id` | C / 38 / 0 | 0 | 331 |
| `bypass_a_p` | C / 32 / 0 | 89 | 30 |
| `bypass_b_p` | C / 32 / 0 | 101 | 29 |
| `bypass_c_p` | C / 32 / 0 | 108 | 33 |

## Data2.zip / Secondary_ExportFeatures.shp

127,403 features; POLYLINE; horizontal CRS EPSG:4326.

| Field | DBF type / width / decimals | Missing | Distinct nonmissing |
|---|---|---:|---:|
| `id` | N / 10 / 0 | 0 | 127,403 |
| `status` | C / 17 / 0 | 0 | 1 |
| `network_ty` | C / 10 / 0 | 0 | 1 |
| `nominal_vo` | C / 9 / 0 | 0 | 5 |
| `usage` | C / 22 / 0 | 0 | 4 |
| `phase_orde` | C / 14 / 0 | 125,641 | 8 |
| `existing_p` | C / 14 / 0 | 34 | 8 |
| `circuit_id` | C / 32 / 0 | 0 | 110 |
| `aep_statio` | C / 40 / 0 | 0 | 31 |
| `aep_circui` | C / 64 / 0 | 0 | 110 |
| `aep_stat_1` | N / 10 / 0 | 0 | 1 |
| `aep_constr` | C / 41 / 0 | 0 | 19 |
| `owner_name` | C / 50 / 0 | 3,236 | 8 |
| `mounting` | C / 11 / 0 | 0 | 3 |
| `report_len` | F / 19 / 11 | 0 | 117,789 |
| `a_phase_sp` | C / 32 / 0 | 85,889 | 115 |
| `b_phase_sp` | C / 32 / 0 | 88,044 | 119 |
| `c_phase_sp` | C / 32 / 0 | 87,169 | 109 |
| `u_phase_sp` | C / 32 / 0 | 118,274 | 99 |
| `n_phase_sp` | C / 32 / 0 | 63 | 175 |
| `spec_name` | C / 32 / 0 | 4 | 156 |
| `aep_date_i` | D / 8 / 0 | 2,439 | 5,744 |
| `treatment_` | D / 8 / 0 | 127,403 | 0 |
| `eo_source_` | C / 35 / 0 | 0 | 2 |
| `esri_defau` | C / 35 / 0 | 0 | 8 |
| `owner_type` | C / 14 / 0 | 0 | 4 |
| `aep_design` | C / 14 / 0 | 0 | 4 |
| `aep_poly_p` | C / 7 / 0 | 0 | 2 |
| `aep_positi` | N / 10 / 0 | 0 | 4 |
| `existing_n` | C / 7 / 0 | 0 | 5 |
| `location_n` | C / 24 / 0 | 324 | 65,014 |
| `location_1` | C / 24 / 0 | 74,409 | 47,871 |
| `shared_neu` | N / 10 / 0 | 0 | 12,638 |
| `cable_coun` | N / 10 / 0 | 0 | 20 |
| `n_cable_co` | N / 10 / 0 | 0 | 12 |
| `global_id` | C / 38 / 0 | 0 | 127,403 |
| `estimated_` | C / 4 / 0 | 127,403 | 0 |
| `Shape_Leng` | F / 19 / 11 | 0 | 127,400 |

## Data2.zip / Switch_Clip.shp

900 features; POINTZ; horizontal CRS EPSG:4326.

| Field | DBF type / width / decimals | Missing | Distinct nonmissing |
|---|---|---:|---:|
| `id` | N / 10 / 0 | 0 | 900 |
| `device_typ` | C / 21 / 0 | 0 | 1 |
| `location_n` | C / 21 / 0 | 0 | 885 |
| `existing_p` | C / 14 / 0 | 3 | 7 |
| `circuit_id` | C / 32 / 0 | 0 | 110 |
| `circuit__1` | C / 32 / 0 | 740 | 83 |
| `aep_statio` | C / 40 / 0 | 0 | 31 |
| `aep_circui` | C / 64 / 0 | 0 | 110 |
| `scada_cont` | C / 12 / 0 | 900 | 0 |
| `normal_sta` | C / 16 / 0 | 0 | 2 |
| `owner_name` | C / 50 / 0 | 0 | 1 |
| `mirrored_i` | C / 7 / 0 | 613 | 1 |
| `aep_out_of` | C / 7 / 0 | 0 | 2 |
| `aep_distri` | C / 7 / 0 | 0 | 1 |
| `aep_switch` | C / 10 / 0 | 893 | 3 |
| `aep_west_l` | C / 21 / 0 | 900 | 0 |
| `a_phase_sp` | C / 32 / 0 | 99 | 41 |
| `b_phase_sp` | C / 32 / 0 | 107 | 41 |
| `c_phase_sp` | C / 32 / 0 | 113 | 41 |
| `a_phase_da` | D / 8 / 0 | 609 | 237 |
| `b_phase_da` | D / 8 / 0 | 609 | 241 |
| `c_phase_da` | D / 8 / 0 | 612 | 239 |
| `upstream_l` | C / 21 / 0 | 900 | 0 |
| `aep_custom` | N / 10 / 0 | 0 | 1 |
| `rotation` | F / 19 / 11 | 0 | 900 |
| `esri_defau` | C / 70 / 0 | 0 | 12 |
| `eo_source_` | C / 35 / 0 | 0 | 1 |
| `status` | C / 17 / 0 | 0 | 1 |
| `owner_type` | C / 14 / 0 | 0 | 1 |
| `mounting` | C / 11 / 0 | 0 | 2 |
| `network_ty` | C / 10 / 0 | 0 | 1 |
| `nominal_vo` | C / 9 / 0 | 0 | 2 |
| `global_id` | C / 38 / 0 | 0 | 900 |

## Data2.zip / Transformer_Clip.shp

26,959 features; POINTZ; horizontal CRS EPSG:4326.

| Field | DBF type / width / decimals | Missing | Distinct nonmissing |
|---|---|---:|---:|
| `id` | N / 10 / 0 | 0 | 26,959 |
| `device_typ` | C / 12 / 0 | 0 | 2 |
| `source_nom` | C / 9 / 0 | 37 | 3 |
| `load_nomin` | C / 9 / 0 | 0 | 6 |
| `existing_p` | C / 14 / 0 | 103 | 8 |
| `circuit_id` | C / 32 / 0 | 0 | 116 |
| `circuit__1` | C / 32 / 0 | 26,921 | 1 |
| `aep_statio` | C / 40 / 0 | 0 | 31 |
| `aep_circui` | C / 64 / 0 | 0 | 116 |
| `scada_cont` | C / 12 / 0 | 26,959 | 0 |
| `owner_name` | C / 50 / 0 | 0 | 1 |
| `aep_custom` | N / 10 / 0 | 0 | 65 |
| `structure_` | C / 13 / 0 | 0 | 5 |
| `aep_west_p` | C / 14 / 0 | 26,959 | 0 |
| `aep_west_l` | C / 21 / 0 | 26,959 | 0 |
| `aep_distri` | C / 7 / 0 | 0 | 1 |
| `location_n` | C / 21 / 0 | 0 | 26,950 |
| `a_phase_sp` | C / 32 / 0 | 15,691 | 41 |
| `b_phase_sp` | C / 32 / 0 | 16,345 | 40 |
| `a_phase_da` | D / 8 / 0 | 3,038 | 8,208 |
| `b_phase_da` | D / 8 / 0 | 3,096 | 8,183 |
| `c_phase_da` | D / 8 / 0 | 3,074 | 8,198 |
| `c_phase_sp` | C / 32 / 0 | 286 | 43 |
| `aep_moved_` | C / 7 / 0 | 321 | 3 |
| `upstream_l` | C / 21 / 0 | 526 | 6,764 |
| `aep_ciac` | C / 4 / 0 | 0 | 2 |
| `ciac_date` | D / 8 / 0 | 26,959 | 0 |
| `esri_defau` | C / 70 / 0 | 0 | 4 |
| `eo_source_` | C / 35 / 0 | 0 | 1 |
| `rotation` | F / 19 / 11 | 0 | 26,949 |
| `global_id` | C / 38 / 0 | 0 | 26,959 |
| `owner_type` | C / 14 / 0 | 0 | 1 |
| `bank_confi` | C / 33 / 0 | 0 | 5 |
| `source_net` | C / 10 / 0 | 0 | 1 |
| `load_netwo` | C / 10 / 0 | 0 | 1 |
| `aep_sec_vo` | C / 29 / 0 | 0 | 17 |
| `mounting` | C / 11 / 0 | 0 | 2 |
| `status` | C / 17 / 0 | 0 | 1 |
