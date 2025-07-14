import { useEffect, type FC } from 'react';
import { useSelector } from 'react-redux';
import Dashboard from './components/Dashboard';
import RequirementsForm from './components/RequirementsForm';
import { selectIsAuthenticated } from './features/auth/authSlice';
import Login from './features/auth/Login';
import { socket } from './socket';

const App: FC = () => {
    const isAuthenticated = useSelector(selectIsAuthenticated);

    useEffect(() => {
        socket.on('connect', () => {
            console.log('Connected to WebSocket');
        });

        socket.on('disconnect', () => {
            console.log('Disconnected from WebSocket');
        });

        return () => {
            socket.off('connect');
            socket.off('disconnect');
        };
    }, []);

    return (
        <div>
            {isAuthenticated ? (
                <>
                    <h1>Welcome to the Agentic AI Development Platform</h1>
                    <Dashboard />
                    <RequirementsForm />
                </>
            ) : (
                <Login />
            )}
        </div>
    );
};

export default App;