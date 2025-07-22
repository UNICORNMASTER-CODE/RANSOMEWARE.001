import { pgTable, text, serial } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

export const scriptConfigurations = pgTable("script_configurations", {
  id: serial("id").primaryKey(),
  password: text("password").notNull(),
  targetLocation: text("target_location").notNull(),
  backupLocation: text("backup_location").notNull(),
  customBackupPath: text("custom_backup_path"),
});

export const insertScriptConfigurationSchema = createInsertSchema(scriptConfigurations).pick({
  password: true,
  targetLocation: true,
  backupLocation: true,
  customBackupPath: true,
});

export type InsertScriptConfiguration = z.infer<typeof insertScriptConfigurationSchema>;
export type ScriptConfiguration = typeof scriptConfigurations.$inferSelect;

// Location options extracted from the provided Python scripts
export const TARGET_LOCATIONS = [
  { value: "~/Desktop/crypto_test", label: "Test Folder (~/Desktop/crypto_test)", category: "safe" },
  { value: "~/Documents", label: "Documents Folder", category: "safe" },
  { value: "~/Desktop", label: "Desktop Folder", category: "safe" },
  { value: "~/Downloads", label: "Downloads Folder", category: "safe" },
  { value: "~", label: "Home Directory", category: "safe" },
  { value: "/", label: "Entire Mac Filesystem (/)", category: "system" },
  { value: "C:\\", label: "Entire Windows Filesystem (C:\\)", category: "system" },
  { value: "/System", label: "Mac System Files (/System)", category: "system" },
  { value: "/usr", label: "Unix System Files (/usr)", category: "system" },
  { value: "/Applications", label: "All Mac Apps (/Applications)", category: "system" },
  { value: "/Library", label: "Mac System Libraries (/Library)", category: "system" },
  { value: "C:\\Windows", label: "Windows System Files", category: "system" },
  { value: "C:\\Program Files", label: "Windows Programs", category: "system" },
  { value: "C:\\Program Files (x86)", label: "32-bit Windows Programs", category: "system" },
];

export const BACKUP_LOCATIONS = [
  { value: "~/Desktop", label: "Desktop" },
  { value: "~/Documents", label: "Documents" },
  { value: "/Volumes/MyUSBDrive", label: "USB Drive (/Volumes/MyUSBDrive)" },
  { value: "/Users/yourusername/SafeBackups", label: "Safe Backups Folder" },
  { value: "custom", label: "Custom Location (User Input)" },
];
