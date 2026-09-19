export type Role='PRODUCTION'|'HSE'|'PRESTATAIRE'|'ADMIN'
export type Status='DRAFT'|'PENDING_APPROVAL'|'ACTIVE'|'SUSPENDED'|'REJECTED'|'COMPLETED'|'CLOSED'
export interface User{id:number;name:string;matricule:string;email:string;role:Role}
export interface Check{code:string;checked:boolean;comment?:string}
export interface Audit{id:number;user_name:string;action:string;details?:string;previous_status?:string;new_status?:string;created_at:string}
export interface Permit{id:number;permit_number:string;permit_date:string;site:string;work_location:string;contractor:string;responsible_person:string;work_description:string;work_types:string[];other_work_type?:string;safety_checks:Check[];gas_measurement:Record<string,unknown>;hot_work_checks:Check[];planned_start_at?:string;expires_at?:string;status:Status;rejection_reason?:string;approval:Record<string,unknown>;closure_checks:Check[];completed_at?:string;closed_at?:string;created_by_id:number;created_at:string;updated_at:string;creator:User;audit_logs:Audit[]}

