
import { useDispatch, useSelector } from 'react-redux';
import { setPage } from '../../store/navigationSlice';

function Footer() {
  const dispatch = useDispatch();
  const currentPage = useSelector(
    (state) => state.navigation.currentPage
  );

  return (
    <footer className="app-footer">
      <button
        disabled={currentPage === 'home'}
        onClick={() => dispatch(setPage('home'))}
      >
        Дом
      </button>

      <button
        disabled={currentPage === 'scenarios'}
        onClick={() => dispatch(setPage('scenarios'))}
      >
        Сценарии
      </button>

      <button
        disabled={currentPage === 'events'}
        onClick={() => dispatch(setPage('events'))}
      >
        Журнал событий
      </button>

      <button
        disabled={currentPage === 'assistant'}
        onClick={() => dispatch(setPage('assistant'))}
      >
        Ассистент
      </button>
    </footer>
  );
}

export default Footer;
