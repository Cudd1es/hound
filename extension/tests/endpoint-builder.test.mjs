import test from 'node:test';
import assert from 'node:assert/strict';

import { buildEndpoint, focusPostingText } from '../sidepanel_helpers.js';

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

test('focusPostingText keeps responsibilities and removes company noise', () => {
  const raw = [
    'Microsoft Software Engineer II',
    'About the job',
    'Overview',
    'Build AI-powered productivity experiences.',
    'Responsibilities',
    '- Ship maintainable services',
    'Qualifications',
    '- 2+ years Python',
    'About the company',
    'Microsoft has 27,623,435 followers',
    'More jobs',
    '- Software Engineer II, Backend'
  ].join('\n');

  const focused = focusPostingText(raw);

  assert.match(focused, /Responsibilities/i);
  assert.match(focused, /Qualifications/i);
  assert.doesNotMatch(focused, /About the company/i);
  assert.doesNotMatch(focused, /More jobs/i);
  assert.ok(focused.length < raw.length);
});

test('focusPostingText returns normalized text for empty section markers', () => {
  const raw = 'Random page wrapper text\nNo explicit heading but has Python and Kubernetes requirements';
  const focused = focusPostingText(raw);
  assert.equal(typeof focused, 'string');
  assert.ok(focused.length > 0);
});
