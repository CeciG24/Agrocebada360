import pandas as pd
import pytest

from ml.data_handoff import climate_provenance, verify_sources, DataHandoffError
from ml.src.provenance import dataset_fingerprint
from ml.align_data import align
from scripts_limpieza.unpack_dataset import extract


@pytest.fixture
def data(tmp_path):
    root = tmp_path / 'dataset'
    files = {
        'parcel_master.csv': 'parcel_id,dataset_split\n001,ENTRENAMIENTO\n002,PREDICCION\n',
        'topografia/topography_master.csv': 'parcel_id\n001\n002\n',
        'targets/rendimiento.csv': 'parcel_id,rendimiento_t_ha\n001,3\n002,\n',
        'features/features_master.csv': 'parcel_id,tmax_mean_c_2025,precip_total_mm_2022\n001,21,5\n002,31,6\n',
        'clima/climate_timeseries.csv': 'parcel_id,fecha_captura,precip_mm,tmin_c,tmax_c\n'
            '001,2022-01-01,5,10,20\n001,2025-04-01,1,10,20\n001,2025-10-01,2,12,22\n001,2025-12-01,9,19,99\n'
            '002,2022-01-01,6,10,20\n002,2025-04-01,1,10,30\n002,2025-10-01,2,12,32\n002,2025-12-01,9,19,99\n',
    }
    for rel, content in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
    schema = {'data_version': dataset_fingerprint(root)['data_version'],
              'features': ['tmax_mean_c_2025', 'precip_total_mm_2022'],
              'prediction_information_cutoff': '2025-10-31'}
    return root, schema


def test_all_features_use_cutoff_and_historical_context(data):
    root, schema = data
    result = climate_provenance(root, schema)
    assert result['features']['tmax_mean_c_2025']['checked_rows'] == 2
    assert result['features']['tmax_mean_c_2025']['max_information_date'] == '2025-10-01'
    assert result['features']['precip_total_mm_2022']['uses_historical_information']
    assert 'no implica' in result['features']['precip_total_mm_2022']['historical_context']
    verify_sources(root, result)


def test_future_temperature_contamination_is_rejected_even_with_new_data_hash(data):
    root, schema = data
    path = root / 'features/features_master.csv'
    df = pd.read_csv(path, dtype={'parcel_id': str})
    df['tmax_mean_c_2025'] = df['tmax_mean_c_2025'].astype(float)
    # Valor contaminado en una feature que no revisaba la antigua muestra de precipitación.
    df.loc[1, 'tmax_mean_c_2025'] = (30 + 32 + 99) / 3
    df.to_csv(path, index=False)
    schema['data_version'] = dataset_fingerprint(root)['data_version']
    with pytest.raises(DataHandoffError, match='tmax_mean_c_2025 no reproduce'):
        climate_provenance(root, schema)


def test_raw_source_change_invalidates_evidence_without_changing_data_version(data):
    root, schema = data
    evidence = climate_provenance(root, schema)
    path = root / 'clima/climate_timeseries.csv'
    path.write_text(path.read_text().replace('19,99', '19,100'), encoding='utf-8')
    assert dataset_fingerprint(root)['data_version'] == schema['data_version']
    with pytest.raises(DataHandoffError, match='Cambió la fuente'):
        verify_sources(root, evidence)


def test_unrecognized_feature_is_not_given_invented_provenance(data):
    root, schema = data
    schema['features'] = ['unavailable_feature']
    with pytest.raises(DataHandoffError, match='No hay transformación'):
        climate_provenance(root, schema)


def test_alignment_preserves_original_bytes_only_after_equivalence(data, tmp_path):
    import shutil
    root, _ = data
    candidate = tmp_path / 'candidate'
    shutil.copytree(root, candidate)
    path = candidate / 'features/features_master.csv'
    path.write_text(path.read_text().replace(',21,', ',21.00000000000001,'), encoding='utf-8')
    output = tmp_path / 'aligned'
    report = align(candidate, root, output)
    assert report['candidate_data_version'] != report['output_data_version']
    assert dataset_fingerprint(output)['data_version'] == dataset_fingerprint(root)['data_version']
    assert (output / 'features/features_master.csv').read_bytes() == (root / 'features/features_master.csv').read_bytes()
    path.write_text(path.read_text().replace('21.00000000000001', '99'), encoding='utf-8')
    with pytest.raises(AssertionError):
        align(candidate, root, tmp_path / 'rejected')
    assert not (tmp_path / 'rejected').exists()


def test_zip_path_escape_rejected_before_extracting(tmp_path):
    from zipfile import ZipFile
    archive = tmp_path / 'invalid.zip'
    with ZipFile(archive, 'w') as z:
        z.writestr('ok.txt', 'ok')
        z.writestr('../escape.txt', 'bad')
    with pytest.raises(ValueError, match='insegura'):
        extract(archive, tmp_path / 'output')
    assert not (tmp_path / 'output/ok.txt').exists()
