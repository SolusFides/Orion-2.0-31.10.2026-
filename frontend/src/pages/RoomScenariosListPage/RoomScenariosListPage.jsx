import { useDispatch } from 'react-redux';
import { setRoom, setPage } from '../../store/navigationSlice';

function RoomScenariosListPage() {
  const dispatch = useDispatch();

  const rooms = [
    { id: 1, name: 'Гостиная' },
    { id: 2, name: 'Кухня' },
    { id: 3, name: 'Спальня' },
    { id: 4, name: 'Ванная' }
  ];

  const openRoomScenarios = (roomId) => {
    dispatch(setRoom(roomId));
    dispatch(setPage('room-scenarios'));
  };

  return (
    <section>
      <button onClick={() => dispatch(setPage('scenarios'))}>
        ← Назад
      </button>

      <h1>Сценарии комнат</h1>

      <div>
        {rooms.map((room) => (
          <button
            key={room.id}
            onClick={() => openRoomScenarios(room.id)}
          >
            {room.name}
          </button>
        ))}
      </div>
    </section>
  );
}

export default RoomScenariosListPage;