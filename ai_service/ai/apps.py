from django.apps import AppConfig
import logging
import os
import sys
import time # Thêm để đo thời gian tải

logger = logging.getLogger('ai')

# Biến global để kiểm tra trạng thái tải (tránh tải lại nếu ready() bị gọi nhiều lần)
chatbot_resources_loaded = False

class AiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ai'

    def ready(self):
        """
        Được Django gọi khi ứng dụng sẵn sàng. Tải tài nguyên chatbot tại đây.
        Sử dụng biến cờ để đảm bảo chỉ tải một lần.
        Kiểm tra 'runserver' trong sys.argv để tránh chạy khi thực hiện các lệnh manage.py khác.
        """
        global chatbot_resources_loaded
        # Chỉ chạy khi lệnh là runserver và chưa tải lần nào
        if os.environ.get('RUN_MAIN') == 'true' and not chatbot_resources_loaded:
            logger.info("AiConfig ready(): RUN_MAIN is true. Attempting to load chatbot resources...")
            start_time = time.time()
            try:
                # Import chatbot_core ở đây là an toàn vì ready() chạy sau khi các app được load
                from . import chatbot_core
                if chatbot_core:
                    # Xác định đường dẫn đến thư mục chứa artifacts
                    # Giả sử artifacts nằm cùng cấp với apps.py trong thư mục 'ai'
                    artifact_dir = os.path.dirname(os.path.abspath(__file__))

                    # Hoặc nếu bạn tạo thư mục con 'artifacts' trong 'ai':
                    # artifact_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'artifacts')

                    logger.info(f"Loading chatbot resources from artifact_dir: {artifact_dir}")

                    # Kiểm tra sự tồn tại của các file quan trọng trước khi load
                    required_files = [
                        'intent_chatbot_model.keras',
                        'symptom_checker_model_filtered.keras',
                        'tokenizer.pickle',
                        'label_encoder.pickle',
                        'relevant_symptom_names_filtered.json',
                        'disease_names_filtered_vi.json',
                        'intents.json'
                        # Thêm các file khác nếu chatbot_core.py cần
                    ]
                    missing_files = []
                    for fname in required_files:
                        fpath = os.path.join(artifact_dir, fname)
                        if not os.path.exists(fpath):
                            missing_files.append(fname)

                    if missing_files:
                        logger.error(f"Cannot load chatbot resources. Missing required artifact files in {artifact_dir}: {', '.join(missing_files)}")
                        # Không đặt chatbot_resources_loaded = True nếu thiếu file
                    else:
                        chatbot_core.load_resources(artifact_dir=artifact_dir)
                        chatbot_resources_loaded = True # Đánh dấu đã tải thành công
                        end_time = time.time()
                        logger.info(f"Chatbot resources loaded successfully via AppConfig in {end_time - start_time:.2f} seconds.")
                        # Lưu trạng thái vào module chatbot_core nếu cần truy cập từ view
                        setattr(chatbot_core, 'resources_ready', True)

                else:
                     logger.error("Could not import chatbot_core in AppConfig.ready(). Ensure the file exists and dependencies are installed.")

            except ImportError as e:
                 logger.critical(f"CRITICAL ImportError loading chatbot_core in AppConfig.ready(): {e}. Please install required libraries from requirements.txt.", exc_info=True)
            except FileNotFoundError as e:
                 logger.critical(f"CRITICAL FileNotFoundError loading chatbot resources in AppConfig.ready(): {e}. Check artifact paths.", exc_info=True)
            except Exception as e:
                logger.critical(f"CRITICAL ERROR loading chatbot resources in AppConfig.ready(): {e}", exc_info=True)
                # Có thể raise lỗi ở đây nếu chatbot là thiết yếu và lỗi tải là nghiêm trọng
                # raise e
        elif chatbot_resources_loaded:
            logger.info("AiConfig ready(): Chatbot resources already loaded.")
        else:
             # Log khi không phải lệnh runserver hoặc RUN_MAIN không được set
             logger.debug(f"AiConfig ready(): Skipping resource loading (RUN_MAIN not 'true' or already loaded). sys.argv: {sys.argv}")
