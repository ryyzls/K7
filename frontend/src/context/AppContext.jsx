import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';

const AppContext = createContext(null);

const USER_KEY = 'carisehat_user';
const FAVORITES_KEY = 'carisehat_favorites';

function readStorage(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

export function AppProvider({ children }) {
  const [user, setUser] = useState(() => readStorage(USER_KEY, null));
  const [loginOpen, setLoginOpen] = useState(false);
  const [toasts, setToasts] = useState([]);
  const [favorites, setFavorites] = useState(() => readStorage(FAVORITES_KEY, []));

  useEffect(() => {
    try {
      if (user) localStorage.setItem(USER_KEY, JSON.stringify(user));
      else localStorage.removeItem(USER_KEY);
    } catch {
      /* localStorage can be unavailable in private mode */
    }
  }, [user]);

  useEffect(() => {
    try {
      localStorage.setItem(FAVORITES_KEY, JSON.stringify(favorites));
    } catch {
      /* ignore */
    }
  }, [favorites]);

  const toast = useCallback((message, tone = 'info') => {
    const id = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
    setToasts((current) => [...current, { id, message, tone }]);
    window.setTimeout(() => {
      setToasts((current) => current.filter((item) => item.id !== id));
    }, 4200);
  }, []);

  const openLogin = useCallback(() => setLoginOpen(true), []);
  const closeLogin = useCallback(() => setLoginOpen(false), []);

  const login = useCallback(
    (provider = 'Google') => {
      const simulated = {
        name: 'Pengguna CariSehat',
        provider,
        signedInAt: new Date().toISOString(),
      };
      setUser(simulated);
      setLoginOpen(false);
      toast(`Masuk sebagai pengguna simulasi via ${provider}.`, 'success');
    },
    [toast],
  );

  const logout = useCallback(() => {
    setUser(null);
    toast('Anda telah keluar dari sesi simulasi.', 'info');
  }, [toast]);

  const toggleFavorite = useCallback(
    (id) => {
      let added = false;
      setFavorites((current) => {
        if (current.includes(id)) return current.filter((item) => item !== id);
        added = true;
        return [...current, id];
      });
      toast(added ? 'Rumah sakit disimpan ke favorit.' : 'Rumah sakit dihapus dari favorit.', added ? 'success' : 'info');
    },
    [toast],
  );

  const value = useMemo(
    () => ({
      user,
      login,
      logout,
      loginOpen,
      openLogin,
      closeLogin,
      toasts,
      toast,
      favorites,
      toggleFavorite,
      isFavorite: (id) => favorites.includes(id),
    }),
    [user, login, logout, loginOpen, openLogin, closeLogin, toasts, toast, favorites, toggleFavorite],
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp() {
  const context = useContext(AppContext);
  if (!context) throw new Error('useApp must be used inside AppProvider');
  return context;
}
