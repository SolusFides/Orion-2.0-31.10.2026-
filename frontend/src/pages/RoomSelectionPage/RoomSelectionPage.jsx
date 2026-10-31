
import { useState } from 'react';

const mockRoomTypes = [
  { id: 1, name: 'Гостиная', icon: '🛋️' },
  { id: 2, name: 'Кухня', icon: '🍽️' },
  { id: 3, name: 'Спальня', icon: '🛏️' },
  { id: 4, name: 'Детская', icon: '🧸' },
  { id: 5, name: 'Ванная', icon: '🛁' },
  { id: 6, name: 'Прихожая', icon: '🚪' },
  { id: 7, name: 'Кабинет', icon: '💻' },
  { id: 8, name: 'Балкон', icon: '🌿' }
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
    <main>
      <h1>Выберите комнаты</h1>

      <p>
        Выберите комнаты вашего дома.
        Для каждой комнаты будут подготовлены подходящие настройки.
      </p>

      <div>
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
