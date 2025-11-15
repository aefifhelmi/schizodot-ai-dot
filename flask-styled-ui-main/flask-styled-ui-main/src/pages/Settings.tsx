import { Card } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Settings as SettingsIcon, Bell, Camera, Database } from "lucide-react";

const Settings = () => {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-3xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-2">Settings</h1>
          <p className="text-muted-foreground">Configure your medication adherence protocol</p>
        </div>

        <div className="space-y-6">
          <Card className="p-6 shadow-card">
            <div className="flex items-center space-x-3 mb-6">
              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                <Camera className="w-5 h-5 text-primary" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-foreground">Camera Settings</h2>
                <p className="text-sm text-muted-foreground">Configure video feed parameters</p>
              </div>
            </div>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label htmlFor="camera-resolution" className="text-foreground">Resolution</Label>
                <Input 
                  id="camera-resolution" 
                  className="w-32" 
                  defaultValue="640x480" 
                />
              </div>
              <div className="flex items-center justify-between">
                <Label htmlFor="frame-rate" className="text-foreground">Frame Rate</Label>
                <Input 
                  id="frame-rate" 
                  className="w-32" 
                  defaultValue="30 FPS" 
                />
              </div>
            </div>
          </Card>

          <Card className="p-6 shadow-card">
            <div className="flex items-center space-x-3 mb-6">
              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                <SettingsIcon className="w-5 h-5 text-primary" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-foreground">Detection Settings</h2>
                <p className="text-sm text-muted-foreground">Adjust protocol parameters</p>
              </div>
            </div>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label htmlFor="confidence" className="text-foreground">Confidence Threshold</Label>
                <Input 
                  id="confidence" 
                  className="w-32" 
                  defaultValue="0.75" 
                />
              </div>
              <div className="flex items-center justify-between">
                <Label htmlFor="stability-frames" className="text-foreground">Stability Frames</Label>
                <Input 
                  id="stability-frames" 
                  className="w-32" 
                  defaultValue="60" 
                />
              </div>
            </div>
          </Card>

          <Card className="p-6 shadow-card">
            <div className="flex items-center space-x-3 mb-6">
              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                <Bell className="w-5 h-5 text-primary" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-foreground">Notifications</h2>
                <p className="text-sm text-muted-foreground">Manage alert preferences</p>
              </div>
            </div>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label htmlFor="session-alerts" className="text-foreground">Session Completion Alerts</Label>
                <Switch id="session-alerts" defaultChecked />
              </div>
              <div className="flex items-center justify-between">
                <Label htmlFor="failure-alerts" className="text-foreground">Failure Alerts</Label>
                <Switch id="failure-alerts" defaultChecked />
              </div>
              <div className="flex items-center justify-between">
                <Label htmlFor="reminder-alerts" className="text-foreground">Schedule Reminders</Label>
                <Switch id="reminder-alerts" defaultChecked />
              </div>
            </div>
          </Card>

          <Card className="p-6 shadow-card">
            <div className="flex items-center space-x-3 mb-6">
              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                <Database className="w-5 h-5 text-primary" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-foreground">Backend Connection</h2>
                <p className="text-sm text-muted-foreground">Configure Flask backend URL</p>
              </div>
            </div>
            <div className="space-y-4">
              <div>
                <Label htmlFor="backend-url" className="text-foreground mb-2 block">Backend URL</Label>
                <Input 
                  id="backend-url" 
                  placeholder="http://localhost:5000" 
                  defaultValue="http://localhost:5000"
                />
              </div>
              <Button className="w-full">Test Connection</Button>
            </div>
          </Card>

          <div className="flex justify-end space-x-3">
            <Button variant="outline">Reset to Defaults</Button>
            <Button>Save Changes</Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;
