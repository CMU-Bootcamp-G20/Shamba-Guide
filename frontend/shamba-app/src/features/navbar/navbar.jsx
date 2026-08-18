import { Link, useLocation } from 'react-router-dom';

function Navbar() {
    const location = useLocation();

    return (
        <header className="app-navbar">
            <div className="nav-brand">
                <span className="logo-icon">🌱</span>
                <h2>ShambaGuide</h2>
            </div>
            
            <nav>
                <Link 
                    to="/" 
                    className={location.pathname === '/' ? 'active' : ''}
                >
                    📊 Imibare (Dashboard)
                </Link>
                <Link 
                    to="/chat" 
                    className={location.pathname === '/chat' ? 'active' : ''}
                >
                    💬 Ikiganiro (Chat)
                </Link>
            </nav>
        </header>
    );
}

export default Navbar;