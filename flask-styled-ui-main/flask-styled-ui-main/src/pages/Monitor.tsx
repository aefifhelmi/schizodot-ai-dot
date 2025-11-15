import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useEffect, useState, useRef } from "react";
import { AlertCircle, CheckCircle2, Loader2, Wifi, WifiOff } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

const Monitor = () => {
  const [protocolStatus, setProtocolStatus] = useState("CONNECTING");
  const [currentPhase, setCurrentPhase] = useState("Waiting for connection...");
  const [phaseCount, setPhaseCount] = useState(0);
  const [isConnected, setIsConnected] = useState(false);
  const [backendUrl] = useState("http://localhost:5000");
  const [isResetting, setIsResetting] = useState(false);
  const { toast } = useToast();
  
  // Use refs to track connection state without causing re-renders
  const connectionStableCount = useRef(0);
  const disconnectionCount = useRef(0);
  const hasShownConnectedToast = useRef(false);
  const hasShownDisconnectedToast = useRef(false);

  useEffect(() => {
    // Poll backend for status updates
    const pollStatus = async () => {
      try {
        const response = await fetch(`${backendUrl}/status_update`);
        if (!response.ok) throw new Error('Backend not responding');
        
        const data = await response.json();
        
        // Connection stability check - require 2 consecutive successes
        connectionStableCount.current++;
        disconnectionCount.current = 0;
        
        if (!isConnected && connectionStableCount.current >= 2) {
          setIsConnected(true);
          if (!hasShownConnectedToast.current) {
            toast({
              title: "Connected to Flask Backend",
              description: "Live monitoring active",
            });
            hasShownConnectedToast.current = true;
            hasShownDisconnectedToast.current = false;
          }
        }
        
        setProtocolStatus(data.result_status || "RUNNING");
        
        // Handle phase - can be either number or string
        const phase = data.current_phase;
        if (typeof phase === 'number') {
          setPhaseCount(phase);
          setCurrentPhase(`Phase ${phase}`);
        } else if (typeof phase === 'string') {
          setCurrentPhase(phase);
          const phaseMatch = phase.match(/Phase (\d+)/);
          if (phaseMatch) {
            setPhaseCount(parseInt(phaseMatch[1]));
          }
        } else {
          setCurrentPhase("Monitoring...");
        }
      } catch (error) {
        // Disconnection stability check - require 3 consecutive failures
        disconnectionCount.current++;
        connectionStableCount.current = 0;
        
        if (isConnected && disconnectionCount.current >= 3) {
          setIsConnected(false);
          if (!hasShownDisconnectedToast.current) {
            toast({
              title: "Connection Lost",
              description: "Reconnecting to Flask backend...",
              variant: "destructive",
            });
            hasShownDisconnectedToast.current = true;
            hasShownConnectedToast.current = false;
          }
          setProtocolStatus("DISCONNECTED");
          setCurrentPhase("Backend not connected");
        }
      }
    };

    // Initial connection
    pollStatus();
    
    // Poll every 500ms for real-time updates
    const interval = setInterval(pollStatus, 500);

    return () => clearInterval(interval);
  }, [backendUrl, toast]);

  const handleReset = async () => {
    setIsResetting(true);
    try {
      const response = await fetch(`${backendUrl}/reset`, {
        method: 'POST',
      });
      
      if (response.ok) {
        toast({
          title: "Protocol Reset",
          description: "Starting new session...",
        });
        setPhaseCount(0);
        setCurrentPhase("Waiting for connection...");
      } else {
        throw new Error('Reset failed');
      }
    } catch (error) {
      toast({
        title: "Reset Failed",
        description: "Could not reset protocol. Please refresh the page.",
        variant: "destructive",
      });
    } finally {
      setIsResetting(false);
    }
  };

  const isSessionTerminated = 
    protocolStatus.includes("PASS") || 
    protocolStatus.includes("FAIL") || 
    protocolStatus.includes("QUIT");

  const getStatusColor = () => {
    if (protocolStatus.includes("PASS") || protocolStatus.includes("VERIFIED")) return "bg-success";
    if (protocolStatus.includes("FAIL") || protocolStatus.includes("FATAL")) return "bg-destructive";
    if (protocolStatus === "DISCONNECTED") return "bg-muted";
    return "bg-warning";
  };

  const getStatusIcon = () => {
    if (protocolStatus.includes("PASS") || protocolStatus.includes("VERIFIED")) return <CheckCircle2 className="w-5 h-5" />;
    if (protocolStatus.includes("FAIL") || protocolStatus.includes("FATAL")) return <AlertCircle className="w-5 h-5" />;
    if (protocolStatus === "DISCONNECTED") return <WifiOff className="w-5 h-5" />;
    return <Loader2 className="w-5 h-5 animate-spin" />;
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-2">💊 Medication Adherence Protocol</h1>
          <p className="text-muted-foreground">Follow the visual instructions on the screen. The process is being monitored in real-time.</p>
        </div>

        <Card className="p-6 shadow-elevated mb-6">
          <div className="relative aspect-video bg-muted rounded-lg flex items-center justify-center border-4 border-border overflow-hidden">
            {isConnected ? (
              <img 
                src={`${backendUrl}/video_feed`}
                alt="Live Video Feed"
                className="w-full h-full object-contain"
                onError={() => {
                  console.error("Video feed error");
                }}
              />
            ) : (
              <div className="text-center p-8">
                <div className="w-24 h-24 mx-auto mb-4 rounded-full bg-primary/10 flex items-center justify-center">
                  <WifiOff className="w-12 h-12 text-muted-foreground animate-pulse" />
                </div>
                <p className="text-muted-foreground mb-2">Waiting for Flask Backend</p>
                <p className="text-xs text-muted-foreground">Run: python proto.py</p>
                <p className="text-xs text-muted-foreground mt-1">Backend URL: {backendUrl}</p>
              </div>
            )}
            
            {/* Connection Status Badge */}
            <div className="absolute top-3 right-3">
              <Badge variant={isConnected ? "default" : "secondary"} className="flex items-center gap-1">
                {isConnected ? <Wifi className="w-3 h-3" /> : <WifiOff className="w-3 h-3" />}
                {isConnected ? "Connected" : "Offline"}
              </Badge>
            </div>
          </div>
        </Card>

        <Card className="p-6 shadow-card mb-6">
          <div className={`${getStatusColor()} text-white rounded-lg p-6 flex items-center justify-between`}>
            <div className="flex items-center space-x-3">
              {getStatusIcon()}
              <span className="font-bold text-lg">Protocol Status: {protocolStatus}</span>
            </div>
            <Badge variant="secondary" className="bg-white/20 text-white">
              Live
            </Badge>
          </div>
          
          {isSessionTerminated && (
            <div className="mt-4 flex justify-center">
              <Button 
                onClick={handleReset}
                disabled={isResetting || !isConnected}
                size="lg"
                className="w-full sm:w-auto"
              >
                {isResetting ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
                {isResetting ? "Resetting..." : "Start New Session"}
              </Button>
            </div>
          )}
        </Card>

        <Card className="p-6 shadow-card">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-medium text-muted-foreground mb-1">Current Phase</h3>
              <p className="text-lg font-semibold text-foreground">{currentPhase}</p>
            </div>
            <div className="text-right">
              <div className="text-3xl font-bold text-primary">{phaseCount}/6</div>
              <div className="text-xs text-muted-foreground">Phases</div>
            </div>
          </div>
          
          <div className="mt-6">
            <div className="flex justify-between mb-2">
              {[1, 2, 3, 4, 5, 6].map((phase) => (
                <div
                  key={phase}
                  className={`w-full h-2 mx-0.5 rounded-full transition-all ${
                    phase <= phaseCount ? "bg-primary" : "bg-muted"
                  }`}
                />
              ))}
            </div>
          </div>
        </Card>

        <div className="mt-6 p-4 bg-accent rounded-lg">
          <h4 className="font-semibold text-sm text-accent-foreground mb-2">Protocol Instructions:</h4>
          <ul className="text-sm text-muted-foreground space-y-1">
            <li>• Keep your face visible in the camera frame</li>
            <li>• Follow each phase as instructed</li>
            <li>• Allow time for detection and verification</li>
            <li>• The process completes automatically upon success</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

// Import Activity icon from lucide-react
import { Activity } from "lucide-react";

export default Monitor;
