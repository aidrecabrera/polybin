import { BinComponent } from "@/components/component/bin";
import { SensorData } from "@/types/sensor.types";
import { AnimatePresence, motion } from "framer-motion";
import {
  BiohazardIcon,
  CircleSlash2,
  LeafIcon,
  RecycleIcon,
} from "lucide-react";
import { useEffect, useState } from "react";
import { io } from "socket.io-client";
import { BannerComponent } from "./components/component/banner";
import { Badge } from "./components/ui/badge";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
} from "./components/ui/card";
import { useSensors } from "./data/useSensors";
import { getPercentage } from "./lib/utils";

const socket = io("http://127.0.0.1:5000");

const bins = [
  { id: 1, title: "Biodegradable", color: "fill-blue-500", icon: LeafIcon },
  {
    id: 2,
    title: "Non-biodegradable",
    color: "fill-yellow-500",
    icon: CircleSlash2,
  },
  { id: 3, title: "Recyclable", color: "fill-green-500", icon: RecycleIcon },
  { id: 4, title: "Hazardous", color: "fill-red-500", icon: BiohazardIcon },
];

function App() {
  const [sensorData, setSensorData] = useState<SensorData | null>(null);
  const { data: binStatus } = useSensors();

  useEffect(() => {
    if (binStatus) {
      setSensorData({
        SENSOR_1: getPercentage(binStatus.SENSOR_1),
        SENSOR_2: getPercentage(binStatus.SENSOR_2),
        SENSOR_3: getPercentage(binStatus.SENSOR_3),
        SENSOR_4: getPercentage(binStatus.SENSOR_4),
      });
    }
  }, [binStatus]);

  useEffect(() => {
    const handleSensorUpdate = (data: SensorData) => {
      setSensorData({
        SENSOR_1: getPercentage(data.SENSOR_1),
        SENSOR_2: getPercentage(data.SENSOR_2),
        SENSOR_3: getPercentage(data.SENSOR_3),
        SENSOR_4: getPercentage(data.SENSOR_4),
      });
    };

    socket.on("sensor_update", handleSensorUpdate);

    return () => {
      socket.off("sensor_update", handleSensorUpdate);
    };
  }, []);

  return (
    <div className="flex flex-col items-center justify-center p-4 space-y-10 md:p-10">
      <BannerComponent />
      <div className="container flex flex-col items-center justify-center flex-grow max-w-6xl gap-4 md:flex-wrap lg:flex-nowrap md:flex-row">
        {bins.map((bin) => (
          <Card className="flex-grow " key={bin.id}>
            <CardHeader className="-mb-6">
              <span className="flex flex-row items-center justify-center w-full gap-2 text-center">
                <bin.icon />
                <h3 className="text-sm font-semibold md:text-md">
                  {bin.title}
                </h3>
              </span>
            </CardHeader>
            <CardContent className="flex items-center justify-center ">
              <BinComponent
                binPathHeightPercent={
                  sensorData
                    ? Math.floor(
                        sensorData[`SENSOR_${bin.id}` as keyof SensorData]
                      )
                    : 0
                }
                color={bin.color}
              />
            </CardContent>
            <CardFooter className="flex items-center justify-center py-4 pb-6 -mt-10">
              <Badge
                variant="outline"
                className="flex items-center gap-2 font-medium"
              >
                <AnimatePresence mode="wait">
                  <motion.p
                    key={
                      sensorData
                        ? sensorData[`SENSOR_${bin.id}` as keyof SensorData]
                        : "0"
                    }
                    initial={{ opacity: 0, y: 1 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -1 }}
                  >
                    <span>
                      Bin is{" "}
                      {sensorData
                        ? sensorData[`SENSOR_${bin.id}` as keyof SensorData] >
                          75
                          ? "Full"
                          : sensorData[`SENSOR_${bin.id}` as keyof SensorData] >
                            50
                          ? "Half"
                          : sensorData[`SENSOR_${bin.id}` as keyof SensorData] >
                            25
                          ? "Low"
                          : "Empty"
                        : "Empty"}
                    </span>{" "}
                    (
                    {sensorData
                      ? `${Math.floor(
                          sensorData[`SENSOR_${bin.id}` as keyof SensorData]
                        )}%`
                      : "0%"}
                    )
                  </motion.p>
                </AnimatePresence>
              </Badge>
            </CardFooter>
          </Card>
        ))}
      </div>
    </div>
  );
}

export default App;
