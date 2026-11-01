
function AssistantPage() {
  return (
    <main className="assistant-page">
      <h1>Ассистент</h1>

      <section>
        <div>
          <div>
            <span>Ассистент</span>
            <p>Вы имеете возможность улучшить ваш умный дом,
                хотите добавить новые устройства?
            </p>
          </div>
        </div>
      </section>

      <form>
        <input
          type="text"
          name="message"
          placeholder="Напишите сообщение..."
        />

        <button type="button" disabled>
          Отправить
        </button>
      </form>
    </main>
  );
}

export default AssistantPage;
