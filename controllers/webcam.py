import cv2
import os

class Webcam:
    def __init__(self, save_path="captures/"):
        self.save_path = save_path
        os.makedirs(self.save_path, exist_ok=True)

    def capture_image(self, filename):
        """
        Captures an image from the webcam and saves it to the specified path.
        :param filename: Name of the file to save.
        """
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Error: Webcam not accessible.")
            return

        print("Press 's' to save the image or 'q' to quit.")
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Failed to grab frame.")
                break

            cv2.imshow("Webcam", frame)
            key = cv2.waitKey(1) & 0xFF

            if key == ord('s'):  # Save the image
                cv2.imwrite(os.path.join(self.save_path, filename), frame)
                print(f"Image saved as {os.path.join(self.save_path, filename)}")
                break
            elif key == ord('q'):  # Quit without saving
                break

        cap.release()
        cv2.destroyAllWindows()

# Example usage
if __name__ == "__main__":
    webcam = Webcam()
    webcam.capture_image("test_image.jpg")
