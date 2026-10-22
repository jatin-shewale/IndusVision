export type Role = "admin" | "engineer" | "supervisor" | "operator";

export interface User {
  id: string;
  name: string;
  email: string;
  role: Role;
  department?: string;
  is_active: boolean;
  created_at: string;
}

export interface Machine {
  id: string;
  machine_id: string;
  name: string;
  location?: string;
  machine_type?: string;
  status: "running" | "idle" | "maintenance" | "fault" | "offline";
  health_score?: number;
  last_seen?: string;
}

export interface SensorReading {
  id: string;
  machine_id: string;
  temperature: number;
  humidity: number;
  vibration: number;
  current_amps: number;
  gas_raw: number;
  distance_cm: number;
  fault: boolean;
  timestamp: string;
}

export interface DetectionItem {
  class_name: string;
  confidence: number;
}

export interface Detection {
  id: string;
  camera_id: string;
  machine_zone?: string;
  detections: DetectionItem[];
  screenshot_path?: string;
  is_violation: boolean;
  timestamp: string;
}

export interface InventoryItem {
  id: string;
  item_name: string;
  category: "raw_material" | "finished_goods" | "scrap";
  quantity: number;
  unit: string;
  threshold: number;
  supplier_id?: string;
  barcode?: string;
  updated_at: string;
  low_stock: boolean;
}

export interface Alert {
  id: string;
  title: string;
  message: string;
  severity: "critical" | "warning" | "info";
  source: "sensor" | "detection" | "inventory" | "manual";
  machine_id?: string;
  status: "open" | "acknowledged" | "resolved";
  created_at: string;
}

export interface MaintenancePrediction {
  id: string;
  machine_id: string;
  health_score: number;
  failure_probability: number;
  remaining_useful_life_days: number;
  predicted_status: "normal" | "warning" | "failure";
  next_maintenance_date: string;
  generated_at: string;
  reasons: string[];
  fault_detected: boolean;
  temperature?: number;
  humidity?: number;
  vibration?: number;
  current_amps?: number;
  gas_raw?: number;
  distance_cm?: number;
}

export interface MaintenanceEvent {
  id: string;
  source: "sensor" | "worker_safety";
  machine_id?: string;
  camera_id?: string;
  title: string;
  status: string;
  causes: string[];
  timestamp: string;
  temperature?: number;
  humidity?: number;
  vibration?: number;
  current_amps?: number;
  gas_raw?: number;
  distance_cm?: number;
}
