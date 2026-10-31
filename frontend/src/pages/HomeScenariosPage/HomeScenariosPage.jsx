import { useDispatch } from 'react-redux';
import { setPage } from '../../store/navigationSlice';

function HomeScenariosPage() {
  const dispatch = useDispatch();

  const scenarios = [
    {
      id: 1,
      name: 'Я ушёл',
      description: 'Выключение света и бытовых приборов',
    },
    {
      id: 2,
      name: 'Я дома',
      description: 'Включение комфортного режима',
    },
    {
      id: 3,
      name: 'Спокойной ночи',
      description: 'Подготовка дома ко сну',
    },
  ];

  function openScenario(scenarioId) {
    console.log('Выбран сценарий дома:', scenarioId);
  }

  function addScenario() {
    console.log('Создание сценария дома');
  }

  return (
    <section>
      <button onClick={() => dispatch(setPage('home'))}>
        ← Назад
      </button>

      <h1>Сценарии дома</h1>

      <div>
        {scenarios.map((scenario) => (
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
        + Добавить сценарий дома
      </button>
    </section>
  );
}

export default HomeScenariosPage;