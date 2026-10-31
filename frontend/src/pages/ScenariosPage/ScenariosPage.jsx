import { useDispatch } from 'react-redux';
import { setPage } from '../../store/navigationSlice';

function ScenariosPage() {
  const dispatch = useDispatch();

  const openHomeScenarios = () => {
    dispatch(setPage('home-scenarios'));
  };

  const openRoomScenarios = () => {
    dispatch(setPage('room-scenarios-list'));
  };

  return (
    <main>
      <h1>Сценарии</h1>

      <button onClick={openHomeScenarios}>
        Сценарии дома
      </button>

      <button onClick={openRoomScenarios}>
        Сценарии комнат
      </button>
    </main>
  );
}

export default ScenariosPage;