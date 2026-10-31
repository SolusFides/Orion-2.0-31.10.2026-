import { useSelector } from 'react-redux';

import Header from '../components/Header/Header';

import HomePage from '../pages/HomePage/HomePage';
import ScenariosPage from '../pages/ScenariosPage/ScenariosPage';
import EventsPage from '../pages/EventsPage/EventsPage';

function App() {
  const currentPage = useSelector(state => state.navigation.currentPage);

  function renderPage() {
    switch (currentPage) {
      case 'home':
        return <HomePage />;

      case 'scenarios':
        return <ScenariosPage />;

      case 'events':
        return <EventsPage />;

      default:
        return <HomePage />;
    }
  }

  return (
    <div>
      <Header />
      {renderPage()}
    </div>
  );
}

export default App;