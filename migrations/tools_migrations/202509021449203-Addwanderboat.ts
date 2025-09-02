import { MigrationInterface, QueryRunner } from "typeorm";

export class Addwanderboat202509021449203 implements MigrationInterface {
    name = 'Addwanderboat202509021449203'

    public async up(queryRunner: QueryRunner): Promise<void> {
        await queryRunner.query(`
            INSERT INTO landing_ia_catalog_item (
                uuid,
                name,
                description,
                short_description,
                logo_url,
                website_url,
                category,
                tags,
                pricing_type,
                pricing_details,
                features,
                use_cases,
                rating,
                reviews_count,
                social_media,
                created_at,
                updated_at,
                is_active,
                metadata
            ) VALUES (
                gen_random_uuid(),
            '',
            '',
            '',
            '',
            '',
            '',
            '[]',
            '',
            '',
            '[]',
            '[]',
            NULL,
            0,
            '{}',
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            true,
            '{}'
            );
        `);
    }

    public async down(queryRunner: QueryRunner): Promise<void> {
        await queryRunner.query(`
            DELETE FROM landing_ia_catalog_item 
            WHERE name = '';
        `);
    }
}
