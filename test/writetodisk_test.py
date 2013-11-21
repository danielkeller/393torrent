import writetodisk
import path
from gi.repository import GLib


class writetodisktest(object)
    def __init__(self)          # class which automatically tests the writetodisk class and all its methods
        info_dict = []          # tuples of directory or just a single file
                                # files should have multimple files larger than a piece and multiple files smaller than a piece
                                
        
        disk_writer = download_directory_manager(info_dict)
                                #creating a new download_directory_manager using the dummy info dict
        download_dir = self.downloads_dir = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOWNLOAD)
        test_download_dir = os.path.join(download_dir, "testdownload")
        does_this_dir_exist = os.path.exists(test_download_dir)
        self.assertTrue(does_this_dir_exist)
        files = get_files_from_info_dict(info_dict)
        
        for f in files
            self.assertTrue(os.path.exists(os.path.join(test_download_dir, f['path'], f['name'])))
        
        # finished testing the created directories and files now time to test pieces
        
        piece1_array = byteArray()
        piece1 =        # create dummy piece with some distinguishable byte sequence
        
        piece2_array = byteArray()
        piece2 =        # create dummy piece with some distinguishable byte sequence other than piece 1
        
        piece3_array = byteArray()
        piece3 =        # create dummy piece with some distinguishable byte sequence other than 1 and 2
        
        piece_final_array = byteArray()
        piece_final =   # create dummy piece with somme distinguishable byte sequence other than 1 or 2 or 3 and make it a different size than the others (which may be the case in the real world!)
        
                        # we will now write pieces to the file and assert that the pieces were placed into the correct locations
        
        disk_writer.write_piece_to_file(piece1)
        
        self.assertTrue(""" open the affected files and verify they have written to the correct spot """)
        
        disk_writer.write_piece_to_file(piece2)
        
        self.assertTrue(""" open the affected files and verify they have written to the correct spot """)
        
        disk_writer.write_piece_to_file(piece3)
        
        self.assertTrue(""" open the affected files and verify they have written to the correct spot """)
        
        disk_writer.write_piece_to_file(piece4)
        
        self.assertTrue(""" open the affected files and verify they have written to the correct spot """)
        
        #fin