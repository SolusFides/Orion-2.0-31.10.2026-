import { useDispatch, useSelector } from 'react-redux';
import { setPage } from '../../store/navigationSlice';
import { setSelectedScenario, clearSelectedScenario } from '../../store/scenarioSlice';

function RoomScenariosPage() {
  const dispatch = useDispatch();

  const selectedRoomId = useSelector(
    (state) => state.navigation.selectedRoomId
  );

  const scenarios = {
  1: [
    {
      id: 1,
      name: 'Вечерний свет',
      description: 'Включить освещение вечером',
      conditions: [
        { id: 1, source: 'Время', operator: '>=', value: '18:00' },
      ],
      logic: 'AND',
      actions: [
        { id: 1, device: 'Умная лампа', command: 'Включить' },
      ],
    },
    {
      id: 2,
      name: 'Кино',
      description: 'Приглушить свет и закрыть шторы',
      conditions: [
        { id: 1, source: 'Пользователь', operator: '=', value: 'Запуск вручную' },
      ],
      logic: 'AND',
      actions: [
        { id: 1, device: 'Умная лампа', command: 'Установить яркость 20%' },
      ],
    },
  ],
  2: [
    {
      id: 3,
      name: 'Приготовление еды',
      description: 'Включить освещение и вытяжку',
      conditions: [],
      logic: 'AND',
      actions: [],
    },
  ],
  3: [
    {
      id: 4,
      name: 'Спокойной ночи',
      description: 'Выключить свет и отключить розетки',
      conditions: [],
      logic: 'AND',
      actions: [],
    },
  ],
  4: [
    {
      id: 5,
      name: 'Защита от протечки',
      description: 'Уведомить при обнаружении воды',
      conditions: [],
      logic: 'AND',
      actions: [],
    },
  ],
 };


  const roomScenarios = scenarios[selectedRoomId] || [];

function openScenario(scenario) {
  dispatch(setSelectedScenario(scenario));
  dispatch(setPage('scenario-editor'));
}

function addScenario() {
  dispatch(clearSelectedScenario());
  dispatch(setPage('scenario-editor'));
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
            onClick={() => openScenario(scenario)}
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