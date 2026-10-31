import { useDispatch, useSelector } from 'react-redux';
import { setPage } from '../../store/navigationSlice';

function RoomScenariosPage() {
  const dispatch = useDispatch();

  const selectedRoomId = useSelector(
    (state) => state.navigation.selectedRoomId
  );

  const scenarios = {
    1: [
      { id: 1, name: 'Вечерний свет', description: 'Включить освещение вечером' },
      { id: 2, name: 'Кино', description: 'Приглушить свет и закрыть шторы' },
    ],
    2: [
      { id: 3, name: 'Приготовление еды', description: 'Включить освещение и вытяжку' },
    ],
    3: [
      { id: 4, name: 'Спокойной ночи', description: 'Выключить свет и отключить розетки' },
    ],
    4: [
      { id: 5, name: 'Защита от протечки', description: 'Уведомить при обнаружении воды' },
    ],
  };

  const roomScenarios = scenarios[selectedRoomId] || [];

  function openScenario(scenarioId) {
    console.log('Выбран сценарий:', scenarioId);
  }

  function addScenario() {
    console.log('Добавление сценария');
  }

  return (
    <section>
      <button onClick={() => dispatch(setPage('room'))}>
        ← Назад
      </button>

      <h1>Сценарии комнаты</h1>

      <div>
        {roomScenarios.map((scenario) => (
          <button
            key={scenario.id}
            onClick={() => openScenario(scenario.id)}
          >
            <h3>{scenario.name}</h3>
            <p>{scenario.description}</p>
          </button>
        ))}
      </div>

      <button onClick={addScenario}>
        + Добавить сценарий
      </button>
    </section>
  );
}

export default RoomScenariosPage;