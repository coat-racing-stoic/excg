import { StrictMode } from 'react';
import ReactDOM from 'react-dom/client';
import { init, isTMA, mockTelegramEnv } from '@tma.js/sdk-react';
import { App } from './App';
import './index.css';

// Check if we're in development mode outside Telegram
const isDev = import.meta.env.DEV;
const isInTelegram = isTMA();

// Mock Telegram environment for development
if (isDev && !isInTelegram) {
  const initDataRaw = new URLSearchParams([
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
    ['auth_date', String(Math.floor(Date.now() / 1000))],
    ['start_param', 'debug'],
    ['chat_type', 'sender'],
    ['chat_instance', '8428209589180549439'],
  ]);

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
  };

  // Build launch params as URLSearchParams string
  const launchParamsStr = new URLSearchParams([
    ['tgWebAppVersion', '8.0'],
    ['tgWebAppPlatform', 'tdesktop'],
    ['tgWebAppThemeParams', JSON.stringify(themeParams)],
    ['tgWebAppData', initDataRaw.toString()],
  ]).toString();

  mockTelegramEnv({
    launchParams: launchParamsStr,
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
