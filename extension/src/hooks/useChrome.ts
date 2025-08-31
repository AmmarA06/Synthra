import { useCallback } from 'react';

export function useChrome() {
  const sendMessage = useCallback((message: any): Promise<any> => {
    return new Promise((resolve, reject) => {
      chrome.runtime.sendMessage(message, (response) => {
        if (chrome.runtime.lastError) {
          reject(new Error(chrome.runtime.lastError.message));
        } else {
          resolve(response);
        }
      });
    });
  }, []);

  const getCurrentTab = useCallback(async () => {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    return tab;
  }, []);

  const getAllTabs = useCallback(async () => {
    return await chrome.tabs.query({});
  }, []);

  const getStorage = useCallback(async (keys?: string[]) => {
    return new Promise((resolve) => {
      chrome.storage.sync.get(keys || null, resolve);
    });
  }, []);

  const setStorage = useCallback(async (items: Record<string, any>) => {
    return new Promise<void>((resolve) => {
      chrome.storage.sync.set(items, resolve);
    });
  }, []);

  return {
    sendMessage,
    getCurrentTab,
    getAllTabs,
    getStorage,
    setStorage
  };
}
