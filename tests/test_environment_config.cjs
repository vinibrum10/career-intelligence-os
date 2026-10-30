// Validate Compose isolation without starting containers or opening a real .env.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {execFileSync} = require('node:child_process');
const root = path.resolve(__dirname, '..');
const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'career-environment-config-'));
const env = {...process.env};
for (const key of ['COMPOSE_PROJECT_NAME','API_PORT','CAREER_APP_IMAGE','POSTGRES_PASSWORD']) delete env[key];
const sha = 'a'.repeat(40);
function config(name) {
  const file = path.join(temp, name + '.env');
  const values = name === 'legacy' ? 'POSTGRES_PASSWORD=synthetic_legacy_password\n' :
    fs.readFileSync(path.join(root, `.env.${name}.example`), 'utf8')
      .replace('replace_with_a_unique_random_hex_password', `synthetic_${name}_password`)
      .replace('replace_with_validated_commit_sha', sha);
  fs.writeFileSync(file, values);
  return JSON.parse(execFileSync('docker', ['compose','--env-file',file,'--file',path.join(root,'compose.yaml'),'config','--format','json'], {env,encoding:'utf8'}));
}
try {
  const legacy = config('legacy'), staging = config('staging'), production = config('production');
  assert.equal(legacy.name, 'career-intelligence-os');
  assert.equal(Number(legacy.services.api.ports[0].published), 8000);
  assert.equal(legacy.services.api.image, 'career-intelligence-os-api');
  assert.equal(staging.name, 'career-staging');
  assert.equal(production.name, 'career-production');
  for (const [model,port] of [[staging,8001],[production,8002]]) {
    assert.equal(model.services.api.ports[0].host_ip, '127.0.0.1');
    assert.equal(Number(model.services.api.ports[0].published), port);
    assert.equal(model.services.db.ports, undefined);
    assert.equal(model.services.db.volumes[0].type, 'volume');
    assert.equal(model.volumes.postgres_data.external, undefined);
    assert.equal(model.networks.default.external, undefined);
  }
  assert.notEqual(staging.volumes.postgres_data.name, production.volumes.postgres_data.name);
  assert.notEqual(staging.networks.default.name, production.networks.default.name);
  assert.notEqual(staging.services.api.environment.DATABASE_URL, production.services.api.environment.DATABASE_URL);
  assert.equal(staging.services.api.image, `career-intelligence-os:${sha}`);
  assert.equal(production.services.api.image, staging.services.api.image);
  console.log('PASS: legacy defaults, separate ports/networks/volumes/credentials and identical release image.');
} finally {
  // Only the two synthetic config files and legacy config created above are removed.
  for (const name of ['legacy','staging','production']) {
    const file = path.join(temp, name + '.env');
    if (fs.existsSync(file)) fs.unlinkSync(file);
  }
  fs.rmdirSync(temp);
}
