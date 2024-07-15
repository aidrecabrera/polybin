import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
} from "@/components/ui/card";
import { SVGProps, useEffect, useState } from "react";
import { JSX } from "react/jsx-runtime";

export default function Dashboard() {
  const [trashcans, setTrashcans] = useState([
    { id: 1, height: 8, status: "Normal" },
    { id: 2, height: 11, status: "Normal" },
    { id: 3, height: 14, status: "Full" },
    { id: 4, height: 6, status: "Normal" },
  ]);
  useEffect(() => {
    const interval = setInterval(() => {
      setTrashcans((prevTrashcans) => {
        return prevTrashcans.map((trashcan) => {
          const randomHeight =
            trashcan.height + Math.floor(Math.random() * 3) - 1;
          const newHeight = randomHeight < 0 ? 0 : randomHeight;
          const newStatus = newHeight <= 13 ? "Full" : "Normal";
          return { ...trashcan, height: newHeight, status: newStatus };
        });
      });
    }, 1000);
    return () => clearInterval(interval);
  }, []);
  return (
    <div className="flex flex-col w-full min-h-screen  ">
      <header className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          Trashscan
        </h1>
        <div className="flex items-center space-x-4">
          <Button variant="ghost">
            <RefreshCwIcon className="w-5 h-5" />
            <span className="sr-only">Refresh</span>
          </Button>
          <Button variant="ghost">
            <SettingsIcon className="w-5 h-5" />
            <span className="sr-only">Settings</span>
          </Button>
        </div>
      </header>
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-6">
        {trashcans.map((trashcan) => (
          <Card
            key={trashcan.id}
            className="bg-white dark:bg-gray-800 shadow-md"
          >
            <CardHeader className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">
                Trashcan {trashcan.id}
              </h2>
              <Badge
                variant={trashcan.status === "Full" ? "destructive" : "default"}
                className="text-xs font-medium"
              >
                {trashcan.status}
              </Badge>
            </CardHeader>
            <CardContent>
              <div className="relative h-48 w-full bg-gray-200 dark:bg-gray-700 rounded-lg overflow-hidden">
                <div
                  className={`absolute right-0 h-full w-[${
                    (trashcan.height / 20) * 100
                  }%] bg-${
                    trashcan.status === "Full" ? "red" : "green"
                  }-500 transition-all duration-500`}
                />
                <div className="absolute inset-0 flex items-center justify-center text-gray-900 dark:text-gray-100 text-2xl font-bold">
                  {trashcan.height} cm
                </div>
              </div>
            </CardContent>
            <CardFooter className="flex items-center justify-between">
              <div className="text-sm text-gray-500 dark:text-gray-400">
                Last updated: {new Date().toLocaleString()}
              </div>
              <Button variant="ghost" size="sm">
                <PlusIcon className="w-4 h-4" />
                <span className="sr-only">More</span>
              </Button>
            </CardFooter>
          </Card>
        ))}
      </div>
    </div>
  );
}

function PlusIcon(props: JSX.IntrinsicAttributes & SVGProps<SVGSVGElement>) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M5 12h14" />
      <path d="M12 5v14" />
    </svg>
  );
}

function RefreshCwIcon(
  props: JSX.IntrinsicAttributes & SVGProps<SVGSVGElement>
) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8" />
      <path d="M21 3v5h-5" />
      <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16" />
      <path d="M8 16H3v5" />
    </svg>
  );
}

function SettingsIcon(
  props: JSX.IntrinsicAttributes & SVGProps<SVGSVGElement>
) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  );
}
