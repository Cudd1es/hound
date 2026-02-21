import test from 'node:test';
import assert from 'node:assert/strict';

import { buildEndpoint } from '../sidepanel_helpers.js';

test('buildEndpoint keeps path prefix when analyze endpoint has prefix', () => {
  const apiUrl = 'http://127.0.0.1:8000/v1/analyze';

  assert.equal(buildEndpoint(apiUrl, 'analyze'), 'http://127.0.0.1:8000/v1/analyze');
  assert.equal(buildEndpoint(apiUrl, 'resume_parse'), 'http://127.0.0.1:8000/v1/resume/parse');
});

test('buildEndpoint supports base URL without analyze suffix', () => {
  const apiUrl = 'http://127.0.0.1:8000/hound-api';

  assert.equal(buildEndpoint(apiUrl, 'analyze'), 'http://127.0.0.1:8000/hound-api/analyze');
  assert.equal(buildEndpoint(apiUrl, 'resume_parse'), 'http://127.0.0.1:8000/hound-api/resume/parse');
});
