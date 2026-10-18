import policy from '../../../api/app/catalogs/regions.json';

const definitions = new Map(policy.regions.map((region) => [region.region_key, region]));
export const regionDefinitionVersion = policy.region_definition_version;
export const regionDefinition = (key) => definitions.get(key);
export const regionLabel = (key) => regionDefinition(key)?.region_label ?? key;
