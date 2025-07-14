import { useState, type FC, type FormEvent } from 'react';
import { useDispatch } from 'react-redux';
import { setToken } from './authSlice';

const Login: FC = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const dispatch = useDispatch();

    const handleLogin = async (e: FormEvent) => {
        e.preventDefault();
        // In a real application, you would make an API call to authenticate
        // and receive a token. For this example, we'll use a dummy token.
        const dummyToken = 'dummy-auth-token';
        dispatch(setToken(dummyToken));
    };

    return (
        <form onSubmit={handleLogin}>
            <div>
                <label htmlFor="username">Username</label>
                <input
                    type="text"
                    id="username"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                />
            </div>
            <div>
                <label htmlFor="password">Password</label>
                <input
                    type="password"
                    id="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                />
            </div>
            <button type="submit">Login</button>
        </form>
    );
};

export default Login;