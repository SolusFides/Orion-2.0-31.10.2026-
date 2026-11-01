
import { useState } from 'react';

const mockRoomTypes = [
  { id: 1, name: 'Гостиная'},
  { id: 2, name: 'Кухня'},
  { id: 3, name: 'Спальня'},
  { id: 4, name: 'Детская'},
  { id: 5, name: 'Ванная'},
  { id: 6, name: 'Прихожая'},
  { id: 7, name: 'Кабинет'},
  { id: 8, name: 'Балкон'}
];

function RoomSelectionPage() {
  const [selectedRooms, setSelectedRooms] = useState([]);

  const handleRoomSelect = (roomId) => {
    setSelectedRooms((prevRooms) =>
      prevRooms.includes(roomId)
        ? prevRooms.filter((id) => id !== roomId)
        : [...prevRooms, roomId]
    );
  };

  return (
    <main className="room-selection-page">
      <h1>Выберите комнаты</h1>

      <p>
        Выберите комнаты вашего дома.
        Для каждой комнаты будут подготовлены подходящие настройки.
      </p>

      <div className="room-options">
        {mockRoomTypes.map((room) => {
          const isSelected = selectedRooms.includes(room.id);

          return (
            <button
              key={room.id}
              type="button"
              onClick={() => handleRoomSelect(room.id)}
              aria-pressed={isSelected}
            >
              {room.icon} {room.name}
              {isSelected && ' ✓'}
            </button>
          );
        })}
      </div>

      <p>Выбрано комнат: {selectedRooms.length}</p>
    </main>
  );
}

export default RoomSelectionPage;
