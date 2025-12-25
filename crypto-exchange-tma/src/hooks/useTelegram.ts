import { useCallback, useMemo, useEffect, useState } from 'react';
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

// Safe wrapper for components that may not be mounted
function safeCall<T>(fn: () => T, fallback: T): T {
  try {
    return fn();
  } catch {
    return fallback;
  }
}

export function useTelegram() {
  // Use camelCase format (true) for launch params
  const launchParams = useLaunchParams(true);
  
  // Safe signal access with fallbacks
  const [theme, setTheme] = useState<Record<string, string>>({});
  const [viewportHeight, setViewportHeight] = useState(window.innerHeight);
  const [isExpanded, setIsExpanded] = useState(true);
  
  // Try to get theme params from signal
  useEffect(() => {
    try {
      if (themeParams.isMounted()) {
        const state = themeParams.state();
        if (state) setTheme(state);
      }
    } catch {
      // Use default theme from launch params
      if (launchParams?.tgWebAppThemeParams) {
        setTheme(launchParams.tgWebAppThemeParams as Record<string, string>);
      }
    }
  }, [launchParams]);
  
  // Try to get viewport info
  useEffect(() => {
    try {
      if (viewport.isMounted()) {
        setViewportHeight(viewport.height() || window.innerHeight);
        setIsExpanded(viewport.isExpanded() ?? true);
      }
    } catch {
      // Use window dimensions as fallback
    }
  }, []);
  
  // tgWebAppData contains the init data with user info
  const user = useMemo(() => launchParams?.tgWebAppData?.user, [launchParams]);
  
  const showBackButton = useCallback(() => {
    safeCall(() => {
      if (backButton.isMounted()) {
        backButton.show();
      }
    }, undefined);
  }, []);
  
  const hideBackButton = useCallback(() => {
    safeCall(() => {
      if (backButton.isMounted()) {
        backButton.hide();
      }
    }, undefined);
  }, []);
  
  const onBackButtonClick = useCallback((callback: () => void) => {
    return safeCall(() => {
      if (backButton.isMounted()) {
        return backButton.onClick(callback);
      }
      return () => {};
    }, () => {});
  }, []);
  
  const setMainButton = useCallback((
    text: string, 
    onClick: () => void,
    options?: { isEnabled?: boolean; isLoading?: boolean }
  ) => {
    return safeCall(() => {
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
    }, () => {});
  }, []);
  
  const hideMainButton = useCallback(() => {
    safeCall(() => {
      if (mainButton.isMounted()) {
        mainButton.hide();
      }
    }, undefined);
  }, []);
  
  const showPopup = useCallback(async (
    title: string, 
    message: string,
    buttons?: Array<{ id?: string; type: 'ok' | 'close' | 'cancel' } | { id?: string; type?: 'default' | 'destructive'; text: string }>
  ) => {
    try {
      if (popup.isSupported()) {
        return await popup.open({ 
          title, 
          message, 
          buttons: buttons || [{ type: 'ok' }] 
        });
      }
    } catch {
      // Fallback to native alert
    }
    alert(`${title}\n${message}`);
    return null;
  }, []);
  
  const vibrate = useCallback((style: 'light' | 'medium' | 'heavy' | 'rigid' | 'soft' = 'medium') => {
    safeCall(() => {
      if (hapticFeedback.isSupported()) {
        hapticFeedback.impactOccurred(style);
      }
    }, undefined);
  }, []);
  
  const notificationVibrate = useCallback((type: 'success' | 'warning' | 'error') => {
    safeCall(() => {
      if (hapticFeedback.isSupported()) {
        hapticFeedback.notificationOccurred(type);
      }
    }, undefined);
  }, []);
  
  const expandViewport = useCallback(() => {
    safeCall(() => {
      if (viewport.isMounted() && !isExpanded) {
        viewport.expand();
      }
    }, undefined);
  }, [isExpanded]);
  
  const close = useCallback(() => {
    safeCall(() => {
      if (miniApp.isMounted()) {
        miniApp.close();
      }
    }, undefined);
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
