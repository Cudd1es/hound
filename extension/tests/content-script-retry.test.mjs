import test from 'node:test';
import assert from 'node:assert/strict';

import {
  isMissingContentScriptReceiverError,
  requestPostingTextFromContentScript
} from '../sidepanel_helpers.js';

test('isMissingContentScriptReceiverError matches chrome no receiver error', () => {
  assert.equal(
    isMissingContentScriptReceiverError(new Error('Could not establish connection. Receiving end does not exist.')),
    true
  );
  assert.equal(isMissingContentScriptReceiverError(new Error('No tab with id: 1')), false);
  assert.equal(isMissingContentScriptReceiverError('Receiving end does not exist.'), true);
});

test('requestPostingTextFromContentScript returns first response without injection', async () => {
  let sendCalls = 0;
  let injectCalls = 0;
  const response = await requestPostingTextFromContentScript({
    tabId: 7,
    sendMessage: async (tabId, message) => {
      sendCalls += 1;
      assert.equal(tabId, 7);
      assert.equal(message?.type, 'hound-extract-posting');
      return { postingText: 'hello' };
    },
    injectScript: async (tabId) => {
      injectCalls += 1;
      assert.equal(tabId, 7);
    }
  });

  assert.equal(response?.postingText, 'hello');
  assert.equal(sendCalls, 1);
  assert.equal(injectCalls, 0);
});

test('requestPostingTextFromContentScript retries once after missing receiver error', async () => {
  let sendCalls = 0;
  let injectCalls = 0;
  const response = await requestPostingTextFromContentScript({
    tabId: 9,
    sendMessage: async () => {
      sendCalls += 1;
      if (sendCalls === 1) {
        throw new Error('Could not establish connection. Receiving end does not exist.');
      }
      return { postingText: 'recovered' };
    },
    injectScript: async (tabId) => {
      injectCalls += 1;
      assert.equal(tabId, 9);
    }
  });

  assert.equal(response?.postingText, 'recovered');
  assert.equal(sendCalls, 2);
  assert.equal(injectCalls, 1);
});

test('requestPostingTextFromContentScript does not inject for unrelated errors', async () => {
  let injectCalls = 0;
  await assert.rejects(
    requestPostingTextFromContentScript({
      tabId: 11,
      sendMessage: async () => {
        throw new Error('Some unrelated runtime error');
      },
      injectScript: async () => {
        injectCalls += 1;
      }
    }),
    /Some unrelated runtime error/
  );
  assert.equal(injectCalls, 0);
});
