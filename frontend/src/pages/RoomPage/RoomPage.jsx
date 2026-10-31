import { useDispatch, useSelector } from 'react-redux';
import { setPage } from '../../store/navigationSlice';

function RoomPage() {
  const dispatch = useDispatch();

  const selectedRoomId = useSelector(
    (state) => state.navigation.selectedRoomId
  );

  const rooms = {
    1: 'Гостиная',
    2: 'Кухня',
    3: 'Спальня',
    4: 'Ванная',
  };

  const roomName = rooms[selectedRoomId] || 'Комната';

  return (
    <section>
      <button onClick={() => dispatch(setPage('home'))}>
        ← Назад
      </button>

      <h1>{roomName}</h1>

      <div>
        <button onClick={() => dispatch(setPage('room-devices'))}>
            <h2>Устройства</h2>
        </button>

        <button onClick={() => dispatch(setPage('room-scenarios'))}>
            <h2>Сценарии</h2>
        </button>
      </div>
    </section>
  );
}

export default RoomPage;