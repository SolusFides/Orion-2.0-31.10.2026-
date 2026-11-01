
import { useSelector } from 'react-redux';

import Footer from '../components/Footer/Footer';
import WelcomePage from '../pages/WelcomePage/WelcomePage';
import LoginPage from '../pages/LoginPage/LoginPage';
import RoomSelectionPage from '../pages/RoomSelectionPage/RoomSelectionPage';
import HomePage from '../pages/HomePage/HomePage';
import ScenariosPage from '../pages/ScenariosPage/ScenariosPage';
import EventsPage from '../pages/EventsPage/EventsPage';
import RoomPage from '../pages/RoomPage/RoomPage';
import RoomDevicesPage from '../pages/RoomDevicesPage/RoomDevicesPage';
import RoomScenariosPage from '../pages/RoomScenariosPage/RoomScenariosPage';
import DevicePage from '../pages/DevicePage/DevicePage';
import HomeScenariosPage from '../pages/HomeScenariosPage/HomeScenariosPage';
import ScenarioEditorPage from '../pages/ScenarioEditorPage/ScenarioEditorPage';
import RoomScenariosListPage from '../pages/RoomScenariosListPage/RoomScenariosListPage';
import AssistantPage from '../pages/AssistantPage/AssistantPage';

function App() {
  const currentPage = useSelector(
    (state) => state.navigation.currentPage
  );

  let page;

  switch (currentPage) {
    case 'welcome':
      page = <WelcomePage />;
      break;
    case 'login':
      page = <LoginPage />;
      break;
    case 'room-selection':
      page = <RoomSelectionPage />;
      break;
    case 'scenarios':
      page = <ScenariosPage />;
      break;
    case 'events':
      page = <EventsPage />;
      break;
    case 'room':
      page = <RoomPage />;
      break;
    case 'room-devices':
      page = <RoomDevicesPage />;
      break;
    case 'room-scenarios':
      page = <RoomScenariosPage />;
      break;
    case 'device':
      page = <DevicePage />;
      break;
    case 'home-scenarios':
      page = <HomeScenariosPage />;
      break;
    case 'scenario-editor':
      page = <ScenarioEditorPage />;
      break;
    case 'room-scenarios-list':
      page = <RoomScenariosListPage />;
      break;
    case 'assistant':
      page = <AssistantPage />;
      break;
    default:
      page = <HomePage />;
  }

  return (
    <div>
      <div>
        <main>{page}</main>
        {currentPage !== 'welcome' &&
          currentPage !== 'login' &&
          <Footer />
        }
      </div>
    </div>
    
  );
}

export default App;
