import { useSelector } from 'react-redux';

import Footer from '../components/Footer/Footer';
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

function App() {
  const currentPage = useSelector(
    (state) => state.navigation.currentPage
  );

  let page;

  switch (currentPage) {
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
    default:
      page = <HomePage />;
  }

  return (
    <>
      <main>{page}</main>
      <Footer />
    </>
  );
}

export default App;