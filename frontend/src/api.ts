const BASE=import.meta.env.VITE_API_URL||'http://localhost:8000/api'
export const token=()=>localStorage.getItem('agil_token')
export async function api<T>(path:string,options:RequestInit={}):Promise<T>{
 const headers=new Headers(options.headers);headers.set('Content-Type','application/json');if(token())headers.set('Authorization',`Bearer ${token()}`)
 const res=await fetch(BASE+path,{...options,headers});if(!res.ok){let message='Erreur serveur';try{const body=await res.json();message=body.detail||message}catch{message='Erreur serveur'}throw new Error(message)}return res.json()
}
