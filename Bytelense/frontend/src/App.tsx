import { ErrorBoundary } from './components/ErrorBoundary';
import { ScanPage } from './components/ScanPage';
import { CameraTest } from './components/CameraTest';
import { SimpleCameraTest } from './components/SimpleCameraTest';

// Set to 'simple' for camera test, 'scan' for full backend integration
const MODE: 'simple' | 'test' | 'scan' = 'simple';

function App() {
  return (
    <ErrorBoundary>
      {MODE === 'simple' ? <SimpleCameraTest /> : MODE === 'test' ? <CameraTest /> : <ScanPage />}
    </ErrorBoundary>
  );
}

export default App;
