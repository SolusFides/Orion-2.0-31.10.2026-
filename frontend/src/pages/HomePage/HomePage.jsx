import { useDispatch } from 'react-redux';
import { setPage, setRoom } from '../../store/navigationSlice';

function HomePage() {
  const dispatch = useDispatch();

  const rooms = [
    { id: 1, name: 'Гостиная', devicesCount: 4 },
    { id: 2, name: 'Кухня', devicesCount: 3 },
    { id: 3, name: 'Спальня', devicesCount: 2 },
    { id: 4, name: 'Ванная', devicesCount: 2 },
  ];

  function openRoom(roomId) {
    dispatch(setRoom(roomId));
    dispatch(setPage('room'));
  }

  function addRoom() {
    console.log('Добавление комнаты');
  }

  return (
    <section>
      <h1>Мой дом</h1>

      <div>
        <h2>Комнаты</h2>

        {rooms.map((room) => (
          <button
            key={room.id}
            onClick={() => openRoom(room.id)}
          >
            <h3>{room.name}</h3>
            <p>Устройств: {room.devicesCount}</p>
          </button>
        ))}
      </div>

      <button onClick={addRoom}>
        + Добавить комнату
      </button>

      <button onClick={() => dispatch(setPage('home-scenarios'))}>
        Сценарии дома
      </button>
    </section>
  );
}

export default HomePage;