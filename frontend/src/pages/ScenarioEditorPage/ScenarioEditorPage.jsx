import { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { setPage } from '../../store/navigationSlice';

function ScenarioEditorPage() {
  const dispatch = useDispatch();

  const selectedScenario = useSelector(
    (state) => state.scenarios.selectedScenario
  );

  const [name, setName] = useState(
    selectedScenario?.name || ''
  );

  const [description, setDescription] = useState(
    selectedScenario?.description || ''
  );

  const [conditions, setConditions] = useState(
    selectedScenario?.conditions || []
  );

  const [logic, setLogic] = useState(
    selectedScenario?.logic || 'AND'
  );

  const [actions, setActions] = useState(
    selectedScenario?.actions || []
  );

  return (
    <section className="scenario-editor">
      <button onClick={() => dispatch(setPage('room-scenarios'))}>
        ← Назад
      </button>

      <h1>
        {selectedScenario
          ? 'Редактирование сценария'
          : 'Новый сценарий'}
      </h1>

      <div>
        <h2>Название сценария</h2>

        <input
          type="text"
          value={name}
          onChange={(event) => setName(event.target.value)}
          placeholder="Введите название сценария"
        />
      </div>

      <div>
        <h2>Описание</h2>

        <textarea
          value={description}
          onChange={(event) => setDescription(event.target.value)}
          placeholder="Описание сценария"
        />
      </div>

      <div>
        <h2>WHEN — Условия запуска</h2>

        {conditions.length > 0 ? (
          conditions.map((condition, index) => (
            <div key={condition.id ?? index}>
              <p>
                {condition.source} {condition.operator} {condition.value}
              </p>
            </div>
          ))
        ) : (
          <p>Условия не добавлены</p>
        )}

        <button onClick={() => console.log('Добавление условия')}>
          + Добавить условие
        </button>
      </div>

      <div>
        <h2>AND / OR — Логика условий</h2>

        <button
          disabled={logic === 'AND'}
          onClick={() => setLogic('AND')}
        >
          AND
        </button>

        <button
          disabled={logic === 'OR'}
          onClick={() => setLogic('OR')}
        >
          OR
        </button>
      </div>

      <div>
        <h2>THEN — Действия</h2>

        {actions.length > 0 ? (
          actions.map((action, index) => (
            <div key={action.id ?? index}>
              <p>
                {action.device}: {action.command}
              </p>
            </div>
          ))
        ) : (
          <p>Действия не добавлены</p>
        )}

        <button onClick={() => console.log('Добавление действия')}>
          + Добавить действие
        </button>
      </div>

      <div>
        <button onClick={() => console.log('Проверка сценария')}>
          Проверить сценарий
        </button>

        <button
          onClick={() => console.log({
            name,
            description,
            conditions,
            logic,
            actions
          })}
        >
          Сохранить сценарий
        </button>
      </div>
    </section>
  );
}

export default ScenarioEditorPage;