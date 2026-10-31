import { useDispatch, useSelector } from 'react-redux';
import { setPage } from '../../store/navigationSlice';

function Header() {
  const dispatch = useDispatch();
  const currentPage = useSelector(state => state.navigation.currentPage);

  return (
    <header>
      <button
        onClick={() => dispatch(setPage('home'))}
        disabled={currentPage === 'home'}
      >
        Дом
      </button>

      <button
        onClick={() => dispatch(setPage('scenarios'))}
        disabled={currentPage === 'scenarios'}
      >
        Сценарии
      </button>

      <button
        onClick={() => dispatch(setPage('events'))}
        disabled={currentPage === 'events'}
      >
        Журнал событий
      </button>
    </header>
  );
}

export default Header;