import { SensorData } from "@/types/sensor.types";
import { useQuery } from "@tanstack/react-query";
import axios from "axios";

const localIpAddress = import.meta.env.VITE_LOCAL_IP_ADDRESS || 'localhost';

export function useSensors() {
  return useQuery<SensorData>({
    queryKey: ["sensor_data"],
    queryFn: async () => {
      const url = `http://${localIpAddress}:5000/sensor_data`;
      const { data } = await axios.get(url);
      return data;
    },
    staleTime: 1000 * 60 * 5,
    gcTime: 1000 * 60 * 30,
    refetchInterval: 2500,
  });
}
