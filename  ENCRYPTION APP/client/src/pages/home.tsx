import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Shield, Settings, Key, FolderOpen, Archive, Edit, Download, Lock, Unlock, TriangleAlert, Info, Code } from "lucide-react";
import { TARGET_LOCATIONS, BACKUP_LOCATIONS, type InsertScriptConfiguration } from "@shared/schema";
import { apiRequest } from "@/lib/queryClient";
import { useToast } from "@/hooks/use-toast";

export default function Home() {
  const { toast } = useToast();
  const [formData, setFormData] = useState<InsertScriptConfiguration>({
    password: "",
    targetLocation: "",
    backupLocation: "",
    customBackupPath: "",
  });
  const [showCustomBackup, setShowCustomBackup] = useState(false);
  const [showGenerated, setShowGenerated] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.password || !formData.targetLocation || !formData.backupLocation) {
      toast({
        title: "Validation Error",
        description: "Please fill in all required fields.",
        variant: "destructive",
      });
      return;
    }

    if (formData.backupLocation === "custom" && !formData.customBackupPath) {
      toast({
        title: "Validation Error",
        description: "Please specify a custom backup path.",
        variant: "destructive",
      });
      return;
    }

    setIsGenerating(true);
    setShowGenerated(true);
    
    setTimeout(() => {
      setIsGenerating(false);
      toast({
        title: "Scripts Generated Successfully",
        description: "Your encryption and decryption scripts are ready for download.",
      });
    }, 1500);
  };

  const downloadScript = async (type: "encrypt" | "decrypt") => {
    try {
      const response = await apiRequest("POST", `/api/scripts/${type}`, formData);
      const blob = await response.blob();
      
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${type}.py`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      toast({
        title: "Download Started",
        description: `${type}.py has been downloaded successfully.`,
      });
    } catch (error) {
      toast({
        title: "Download Failed",
        description: "Failed to generate and download the script. Please try again.",
        variant: "destructive",
      });
    }
  };

  return (
    <div className="bg-gray-50 min-h-screen">
      {/* Header Section */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <div className="flex items-center space-x-3">
            <div className="bg-primary p-3 rounded-lg">
              <Shield className="text-primary-foreground w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">File Encryption Script Generator</h1>
              <p className="text-gray-600 mt-1">Generate customized Python encryption and decryption scripts</p>
            </div>
          </div>
        </div>
      </header>

      {/* Warning Banner */}
      <div className="bg-orange-50 border-l-4 border-orange-400 p-4 max-w-4xl mx-auto mt-6">
        <div className="flex">
          <div className="flex-shrink-0">
            <TriangleAlert className="text-orange-400 w-5 h-5" />
          </div>
          <div className="ml-3">
            <p className="text-sm text-orange-800">
              <span className="font-medium">Important:</span> This tool generates powerful encryption scripts. Use responsibly and always create backups before running encryption. Test on non-critical files first.
            </p>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 py-8">
        
        {/* Configuration Form */}
        <Card className="mb-8">
          <CardContent className="p-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-6 flex items-center">
              <Settings className="text-primary mr-3 w-5 h-5" />
              Configuration Settings
            </h2>
            
            <form onSubmit={handleSubmit} className="space-y-6">
              
              {/* Password Field */}
              <div>
                <Label htmlFor="password" className="flex items-center text-sm font-medium text-gray-700 mb-2">
                  <Key className="text-gray-400 mr-2 w-4 h-4" />
                  Encryption Password
                </Label>
                <Input 
                  id="password" 
                  type="text"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  placeholder="Enter your encryption password"
                  required
                  className="w-full"
                />
                <p className="text-xs text-gray-500 mt-1">Password will be visible in the generated script for clarity</p>
              </div>

              {/* Target Location Dropdown */}
              <div>
                <Label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                  <FolderOpen className="text-gray-400 mr-2 w-4 h-4" />
                  Target Location for Encryption
                </Label>
                <Select value={formData.targetLocation} onValueChange={(value) => setFormData({ ...formData, targetLocation: value })}>
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select target location..." />
                  </SelectTrigger>
                  <SelectContent>
                    <div className="px-2 py-1 text-sm font-medium text-gray-500">Safe Options (Recommended)</div>
                    {TARGET_LOCATIONS.filter(loc => loc.category === "safe").map(location => (
                      <SelectItem key={location.value} value={location.value}>
                        {location.label}
                      </SelectItem>
                    ))}
                    <div className="px-2 py-1 text-sm font-medium text-gray-500 mt-2">System-Wide Options (Advanced)</div>
                    {TARGET_LOCATIONS.filter(loc => loc.category === "system").map(location => (
                      <SelectItem key={location.value} value={location.value}>
                        {location.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-xs text-gray-500 mt-1">Choose carefully - system-wide options can affect critical files</p>
              </div>

              {/* Backup Location Dropdown */}
              <div>
                <Label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                  <Archive className="text-gray-400 mr-2 w-4 h-4" />
                  Backup Location
                </Label>
                <Select 
                  value={formData.backupLocation} 
                  onValueChange={(value) => {
                    setFormData({ ...formData, backupLocation: value });
                    setShowCustomBackup(value === "custom");
                  }}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select backup location..." />
                  </SelectTrigger>
                  <SelectContent>
                    {BACKUP_LOCATIONS.map(location => (
                      <SelectItem key={location.value} value={location.value}>
                        {location.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-xs text-gray-500 mt-1">Backups will be created before encryption starts</p>
              </div>

              {/* Custom Backup Location */}
              {showCustomBackup && (
                <div>
                  <Label htmlFor="customBackupPath" className="flex items-center text-sm font-medium text-gray-700 mb-2">
                    <Edit className="text-gray-400 mr-2 w-4 h-4" />
                    Custom Backup Path
                  </Label>
                  <Input 
                    id="customBackupPath"
                    type="text"
                    value={formData.customBackupPath}
                    onChange={(e) => setFormData({ ...formData, customBackupPath: e.target.value })}
                    placeholder="/path/to/your/backup/location"
                    className="w-full"
                  />
                </div>
              )}

              {/* Generate Button */}
              <div className="pt-4">
                <Button 
                  type="submit" 
                  disabled={isGenerating}
                  className="w-full bg-primary hover:bg-primary/90 text-primary-foreground font-semibold py-4 px-6 h-auto space-x-3 shadow-lg hover:shadow-xl"
                >
                  <Code className="w-5 h-5" />
                  <span>{isGenerating ? "Generating Scripts..." : "Generate Encryption Scripts"}</span>
                </Button>
              </div>

            </form>
          </CardContent>
        </Card>

        {/* Generated Files Section */}
        {showGenerated && (
          <Card className="mb-8">
            <CardContent className="p-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-6 flex items-center">
                <Download className="text-green-500 mr-3 w-5 h-5" />
                Generated Files
              </h2>
              
              <div className="grid md:grid-cols-2 gap-6">
                
                {/* Encryption Script */}
                <div className="border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
                  <div className="flex items-start space-x-4">
                    <div className="bg-red-100 p-3 rounded-lg">
                      <Lock className="text-red-600 w-6 h-6" />
                    </div>
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-900 mb-2">encrypt.py</h3>
                      <p className="text-sm text-gray-600 mb-4">Encrypts files in the selected location with automatic backup</p>
                      <Button 
                        onClick={() => downloadScript("encrypt")}
                        className="bg-red-500 hover:bg-red-600 text-white"
                        size="sm"
                      >
                        <Download className="w-4 h-4 mr-2" />
                        Download
                      </Button>
                    </div>
                  </div>
                </div>

                {/* Decryption Script */}
                <div className="border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
                  <div className="flex items-start space-x-4">
                    <div className="bg-green-100 p-3 rounded-lg">
                      <Unlock className="text-green-600 w-6 h-6" />
                    </div>
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-900 mb-2">decrypt.py</h3>
                      <p className="text-sm text-gray-600 mb-4">Decrypts files that were encrypted with the corresponding encrypt.py</p>
                      <Button 
                        onClick={() => downloadScript("decrypt")}
                        className="bg-green-500 hover:bg-green-600 text-white"
                        size="sm"
                      >
                        <Download className="w-4 h-4 mr-2" />
                        Download
                      </Button>
                    </div>
                  </div>
                </div>

              </div>

              {/* Usage Instructions */}
              <Alert className="mt-8 bg-blue-50 border-blue-200">
                <Info className="w-4 h-4 text-blue-600" />
                <AlertDescription className="text-blue-800">
                  <h4 className="font-semibold mb-3 flex items-center">
                    Usage Instructions
                  </h4>
                  <ol className="text-sm space-y-2 list-decimal list-inside">
                    <li>Download both scripts to a safe location</li>
                    <li>Run <code className="bg-blue-100 px-2 py-1 rounded">encrypt.py</code> to encrypt files (backup will be created automatically)</li>
                    <li>Use <code className="bg-blue-100 px-2 py-1 rounded">decrypt.py</code> to restore files when needed</li>
                    <li>Keep your password secure - it's required for decryption</li>
                  </ol>
                </AlertDescription>
              </Alert>

            </CardContent>
          </Card>
        )}

        {/* Features Section */}
        <Card>
          <CardContent className="p-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-6">Features</h2>
            
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              
              <div className="flex items-start space-x-3">
                <div className="bg-green-100 p-2 rounded-lg">
                  <Shield className="text-green-600 w-5 h-5" />
                </div>
                <div>
                  <h4 className="font-semibold text-gray-900">Automatic Backups</h4>
                  <p className="text-sm text-gray-600">Creates timestamped backups before encryption</p>
                </div>
              </div>
              
              <div className="flex items-start space-x-3">
                <div className="bg-blue-100 p-2 rounded-lg">
                  <Key className="text-blue-600 w-5 h-5" />
                </div>
                <div>
                  <h4 className="font-semibold text-gray-900">Password-Based</h4>
                  <p className="text-sm text-gray-600">Uses PBKDF2 key derivation for security</p>
                </div>
              </div>
              
              <div className="flex items-start space-x-3">
                <div className="bg-purple-100 p-2 rounded-lg">
                  <FolderOpen className="text-purple-600 w-5 h-5" />
                </div>
                <div>
                  <h4 className="font-semibold text-gray-900">Directory Structure</h4>
                  <p className="text-sm text-gray-600">Maintains folder hierarchy in backups</p>
                </div>
              </div>
              
              <div className="flex items-start space-x-3">
                <div className="bg-orange-100 p-2 rounded-lg">
                  <Archive className="text-orange-600 w-5 h-5" />
                </div>
                <div>
                  <h4 className="font-semibold text-gray-900">Smart Exclusions</h4>
                  <p className="text-sm text-gray-600">Avoids encrypting script files themselves</p>
                </div>
              </div>
              
              <div className="flex items-start space-x-3">
                <div className="bg-red-100 p-2 rounded-lg">
                  <TriangleAlert className="text-red-600 w-5 h-5" />
                </div>
                <div>
                  <h4 className="font-semibold text-gray-900">Error Handling</h4>
                  <p className="text-sm text-gray-600">Continues operation even if some files fail</p>
                </div>
              </div>
              
              <div className="flex items-start space-x-3">
                <div className="bg-indigo-100 p-2 rounded-lg">
                  <Download className="text-indigo-600 w-5 h-5" />
                </div>
                <div>
                  <h4 className="font-semibold text-gray-900">Progress Tracking</h4>
                  <p className="text-sm text-gray-600">Shows detailed progress during operation</p>
                </div>
              </div>
              
            </div>
          </CardContent>
        </Card>

      </main>

      {/* Footer */}
      <footer className="bg-gray-800 text-gray-400 py-8 mt-12">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <p className="text-sm">
            <TriangleAlert className="text-orange-400 mr-2 w-4 h-4 inline" />
            Use this tool responsibly. Always test on non-critical files first.
          </p>
        </div>
      </footer>

    </div>
  );
}
