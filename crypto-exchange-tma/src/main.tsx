import { StrictMode } from 'react';
import ReactDOM from 'react-dom/client';
import { init, isTMA, mockTelegramEnv, emitEvent } from '@tma.js/sdk-react';
import { App } from './App';
import './index.css';

// Check if we're in development mode outside Telegram
const isDev = import.meta.env.DEV;
const isInTelegram = isTMA();

// Theme params for mock environment
const themeParams = {
  accent_text_color: '#6ab2f2',
  bg_color: '#17212b',
  button_color: '#5288c1',
  button_text_color: '#ffffff',
  destructive_text_color: '#ec3942',
  header_bg_color: '#17212b',
  hint_color: '#708499',
  link_color: '#6ab3f3',
  secondary_bg_color: '#232e3c',
  section_bg_color: '#17212b',
  section_header_text_color: '#6ab3f3',
  subtitle_text_color: '#708499',
  text_color: '#f5f5f5',
} as const;

const noInsets = {
  left: 0,
  top: 0,
  bottom: 0,
  right: 0,
} as const;

// Mock Telegram environment for development (v3 format)
if (isDev && !isInTelegram) {
  mockTelegramEnv({
    launchParams: {
      tgWebAppThemeParams: themeParams,
      tgWebAppData: new URLSearchParams([
        ['user', JSON.stringify({
          id: 99281932,
          first_name: 'Test',
          last_name: 'User',
          username: 'testuser',
          language_code: 'ru',
          is_premium: true,
          allows_write_to_pm: true,
        })],
        ['hash', '89d6079ad6762351f38c6dbbc41bb53048019256a9443988af7a48bcad16ba31'],
        ['signature', 'test_signature_value'],
        ['auth_date', Date.now().toString()],
      ]),
      tgWebAppStartParam: 'debug',
      tgWebAppVersion: '8',
      tgWebAppPlatform: 'tdesktop',
    },
    onEvent(event) {
      // Handle SDK events in mock environment
      if (event.name === 'web_app_request_theme') {
        return emitEvent('theme_changed', { theme_params: themeParams });
      }
      if (event.name === 'web_app_request_viewport') {
        return emitEvent('viewport_changed', {
          height: window.innerHeight,
          width: window.innerWidth,
          is_expanded: true,
          is_state_stable: true,
        });
      }
      if (event.name === 'web_app_request_content_safe_area') {
        return emitEvent('content_safe_area_changed', noInsets);
      }
      if (event.name === 'web_app_request_safe_area') {
        return emitEvent('safe_area_changed', noInsets);
      }
      // Log unhandled events for debugging
      console.log('📱 TMA Event:', event.name, event.params);
    },
  });
  console.log('🔧 Development mode: Telegram environment mocked');
}

async function bootstrap() {
  const root = ReactDOM.createRoot(document.getElementById('root')!);
  
  // In dev mode or in Telegram - show the app
  const shouldShowApp = isDev || isInTelegram;
  
  if (shouldShowApp) {
    // Initialize TMA SDK
    try {
      init();
    } catch (e) {
      console.warn('TMA SDK init failed:', e);
    }
  }
  
  root.render(
    <StrictMode>
      <App />
    </StrictMode>
  );
}

bootstrap();
