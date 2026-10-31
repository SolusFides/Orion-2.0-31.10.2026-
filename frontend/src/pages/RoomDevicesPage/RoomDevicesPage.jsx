import { useDispatch, useSelector } from 'react-redux';
import { setPage } from '../../store/navigationSlice';

function RoomDevicesPage() {
  const dispatch = useDispatch();

  const selectedRoomId = useSelector(
    (state) => state.navigation.selectedRoomId
  );

  const devices = {
    1: [
      { id: 1, name: 'Умная лампа', state: 'Включена', online: true },
      { id: 2, name: 'Кондиционер', state: 'Выключен', online: true },
      { id: 3, name: 'Датчик температуры', state: '22 °C', online: true },
      { id: 4, name: 'Датчик движения', state: 'Нет движения', online: false },
    ],
    2: [
      { id: 5, name: 'Умная розетка', state: 'Включена', online: true },
      { id: 6, name: 'Датчик дыма', state: 'Норма', online: true },
      { id: 7, name: 'Освещение', state: 'Выключено', online: true },
    ],
    3: [
      { id: 8, name: 'Умная лампа', state: 'Выключена', online: true },
      { id: 9, name: 'Датчик температуры', state: '21 °C', online: true },
    ],
    4: [
      { id: 10, name: 'Датчик протечки', state: 'Норма', online: true },
      { id: 11, name: 'Вентиляция', state: 'Включена', online: false },
    ],
  };

  const roomDevices = devices[selectedRoomId] || [];

  function openDevice(deviceId) {
    console.log('Выбрано устройство:', deviceId);
  }

  function addDevice() {
    console.log('Добавление устройства');
  }

  return (
    <section>
      <button onClick={() => dispatch(setPage('room'))}>
        ← Назад
      </button>

      <h1>Устройства комнаты</h1>

      <div>
        {roomDevices.map((device) => (
          <button
            key={device.id}
            onClick={() => openDevice(device.id)}
          >
            <h3>{device.name}</h3>
            <p>Состояние: {device.state}</p>
            <p>
              Подключение: {device.online ? 'В сети' : 'Не в сети'}
            </p>
          </button>
        ))}
      </div>

      <button onClick={addDevice}>
        + Добавить устройство
      </button>
    </section>
  );
}

export default RoomDevicesPage;