-- Add attachments column to five_w_one_h table
ALTER TABLE `five_w_one_h` ADD COLUMN `attachments` JSON DEFAULT NULL AFTER `attachment_path`;

-- Verify the column was added
DESCRIBE `five_w_one_h`;
