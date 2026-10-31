function EventsPage() {
  const events = [
    {
      id: 1,
      name: 'Умная лампа',
      description: 'Устройство включено',
      date: '01.11.2026 18:30',
      room: 'Гостиная',
      type: 'device_state'
    },
    {
      id: 2,
      name: 'Датчик движения',
      description: 'Обнаружено движение',
      date: '01.11.2026 18:25',
      room: 'Коридор',
      type: 'device_event'
    },
    {
      id: 3,
      name: 'Вечерний свет',
      description: 'Сценарий успешно выполнен',
      date: '01.11.2026 18:00',
      room: 'Гостиная',
      type: 'scenario'
    }
  ];

  return (
    <section>
      <h1>Журнал событий</h1>

      <div>
        {events.map((event) => (
          <div key={event.id}>
            <h3>{event.name}</h3>
            <p>{event.description}</p>
            <p>{event.room}</p>
            <p>{event.date}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

export default EventsPage;