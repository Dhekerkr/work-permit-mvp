import {createContext,useContext,useEffect,useState,type ReactNode} from 'react'
import {api} from './api';import type{User}from'./types'
type Ctx={user:User|null;loading:boolean;login:(identifier:string,password:string)=>Promise<void>;logout:()=>void}
const AuthContext=createContext<Ctx>(null!)
export function AuthProvider({children}:{children:ReactNode}){const[user,setUser]=useState<User|null>(null);const[loading,setLoading]=useState(true);useEffect(()=>{if(localStorage.getItem('agil_token'))api<User>('/auth/me').then(setUser).catch(()=>localStorage.removeItem('agil_token')).finally(()=>setLoading(false));else setLoading(false)},[]);async function login(identifier:string,password:string){const r=await api<{access_token:string;user:User}>('/auth/login',{method:'POST',body:JSON.stringify({identifier,password})});localStorage.setItem('agil_token',r.access_token);setUser(r.user)}function logout(){localStorage.removeItem('agil_token');setUser(null)}return <AuthContext.Provider value={{user,loading,login,logout}}>{children}</AuthContext.Provider>}
export const useAuth=()=>useContext(AuthContext)

