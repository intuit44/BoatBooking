import { useDispatch, useSelector, TypedUseSelectorHook } from App.tsx;
import type { RootState, AppDispatch } from './store';

// Hooks tipados para usar en toda la aplicación
export const useAppDispatch = () => useDispatch<AppDispatch>();
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;