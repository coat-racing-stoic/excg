import { useCallback, useMemo } from 'react';
import {
  backButton,
  mainButton,
  popup,
  hapticFeedback,
  themeParams,
  viewport,
  miniApp,
  useSignal,
  useLaunchParams,
} from '@tma.js/sdk-react';

export function useTelegram() {
  const launchParams = useLaunchParams(true);
  const theme = useSignal(themeParams.state);
  const viewportHeight = useSignal(viewport.height);
  const isExpanded = useSignal(viewport.isExpanded);
  
  // tgWebAppData contains the init data with user info
  const user = useMemo(() => launchParams?.tgWebAppData?.user, [launchParams]);
  
  const showBackButton = useCallback(() => {
    if (backButton.isMounted()) {
      backButton.show();
    }
  }, []);
  
  const hideBackButton = useCallback(() => {
    if (backButton.isMounted()) {
      backButton.hide();
    }
  }, []);
  
  const onBackButtonClick = useCallback((callback: () => void) => {
    if (backButton.isMounted()) {
      return backButton.onClick(callback);
    }
    return () => {};
  }, []);
  
  const setMainButton = useCallback((
    text: string, 
    onClick: () => void,
    options?: { isEnabled?: boolean; isLoading?: boolean }
  ) => {
    if (mainButton.isMounted()) {
      mainButton.setParams({ 
        text, 
        isVisible: true,
        isEnabled: options?.isEnabled ?? true,
        isLoaderVisible: options?.isLoading ?? false,
      });
      return mainButton.onClick(onClick);
    }
    return () => {};
  }, []);
  
  const hideMainButton = useCallback(() => {
    if (mainButton.isMounted()) {
      mainButton.hide();
    }
  }, []);
  
  const showPopup = useCallback(async (
    title: string, 
    message: string,
    buttons?: Array<{ id?: string; type: 'ok' | 'close' | 'cancel' } | { id?: string; type?: 'default' | 'destructive'; text: string }>
  ) => {
    if (popup.isSupported()) {
      return popup.show({ 
        title, 
        message, 
        buttons: buttons || [{ type: 'ok' }] 
      });
    }
    alert(`${title}\n${message}`);
    return null;
  }, []);
  
  const vibrate = useCallback((style: 'light' | 'medium' | 'heavy' | 'rigid' | 'soft' = 'medium') => {
    if (hapticFeedback.isSupported()) {
      hapticFeedback.impactOccurred(style);
    }
  }, []);
  
  const notificationVibrate = useCallback((type: 'success' | 'warning' | 'error') => {
    if (hapticFeedback.isSupported()) {
      hapticFeedback.notificationOccurred(type);
    }
  }, []);
  
  const expandViewport = useCallback(() => {
    if (viewport.isMounted() && !isExpanded) {
      viewport.expand();
    }
  }, [isExpanded]);
  
  const close = useCallback(() => {
    if (miniApp.isMounted()) {
      miniApp.close();
    }
  }, []);
  
  return {
    user,
    theme,
    viewportHeight,
    isExpanded,
    launchParams,
    showBackButton,
    hideBackButton,
    onBackButtonClick,
    setMainButton,
    hideMainButton,
    showPopup,
    vibrate,
    notificationVibrate,
    expandViewport,
    close,
  };
}
